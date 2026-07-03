import stripe
import logging
from django.conf import settings
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from clientes.models import Client

logger = logging.getLogger(__name__)

# Configure Stripe key (we'll set this in settings later)
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')

@login_required
def create_checkout_session(request):
    """
    Creates a Stripe Checkout Session for upgrading storage (Add-on).
    """
    tenant = request.tenant
    price_id = request.GET.get('price_id') # e.g., the ID of the 10GB or 50GB plan
    
    if not price_id:
        return JsonResponse({'error': 'price_id is required'}, status=400)
        
    try:
        # Define success/cancel URLs based on the current tenant domain
        domain = request.get_host()
        protocol = 'https' if request.is_secure() else 'http'
        base_url = f"{protocol}://{domain}"
        
        # Determine if we should create a new customer or use existing
        customer_id = tenant.stripe_customer_id
        
        # Check if the price is a base plan (needs trial) or an addon
        price_boutique = getattr(settings, 'STRIPE_PRICE_BOUTIQUE', '')
        price_corporate = getattr(settings, 'STRIPE_PRICE_CORPORATE', '')
        is_base_plan = price_id in [price_boutique, price_corporate]
        
        # Base arguments for the session
        session_kwargs = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price': price_id,
                'quantity': 1,
            }],
            'mode': 'subscription', 
            'success_url': f"{base_url}/crm/assinatura/?checkout=success",
            'cancel_url': f"{base_url}/crm/assinatura/?checkout=canceled",
            'client_reference_id': str(tenant.id),
            'metadata': {
                'tenant_id': str(tenant.id),
                'tenant_schema': tenant.schema_name
            }
        }
        
        if is_base_plan:
            session_kwargs['subscription_data'] = {
                'trial_period_days': 14,
            }
        
        if customer_id:
            session_kwargs['customer'] = customer_id
        else:
            session_kwargs['customer_email'] = request.user.email

        session = stripe.checkout.Session.create(**session_kwargs)
        return redirect(session.url)
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def stripe_customer_portal(request):
    """
    Creates a Stripe Customer Portal session so the user can manage their subscription (cancel, downgrade, update card).
    """
    tenant = request.tenant
    
    if not tenant.stripe_customer_id:
        return redirect('core:assinatura')
        
    try:
        domain = request.get_host()
        protocol = 'https' if request.is_secure() else 'http'
        return_url = f"{protocol}://{domain}/crm/assinatura/"
        
        session = stripe.billing_portal.Session.create(
            customer=tenant.stripe_customer_id,
            return_url=return_url,
        )
        return redirect(session.url)
    except Exception as e:
        logger.error(f"Error creating customer portal session: {str(e)}")
        return redirect('core:assinatura')

@csrf_exempt
def stripe_webhook(request):
    """
    Handles Stripe webhooks for subscription updates.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    
    event = None
    
    if endpoint_secret:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            return HttpResponse(status=400) # Invalid payload
        except stripe.error.SignatureVerificationError as e:
            return HttpResponse(status=400) # Invalid signature
    else:
        # Fallback if webhook secret is not set (e.g., local dev without CLI)
        # Not recommended for production, but useful if they are lazy
        try:
            import json
            event_dict = json.loads(payload)
            # Create a mock event object for simple parsing
            class MockEvent: pass
            event = MockEvent()
            event.type = event_dict.get('type')
            event.data = MockEvent()
            event.data.object = event_dict.get('data', {}).get('object', {})
        except Exception:
            return HttpResponse(status=400)
            
    # Handle the event
    if event.type == 'checkout.session.completed':
        session = event.data.object
        # Retrieve tenant via client_reference_id
        tenant_id = getattr(session, 'client_reference_id', None)
        customer_id = getattr(session, 'customer', None)
        subscription_id = getattr(session, 'subscription', None)
        
        if tenant_id:
            try:
                tenant = Client.objects.get(id=tenant_id)
                tenant.stripe_customer_id = customer_id
                tenant.stripe_subscription_id = subscription_id
                tenant.status_assinatura = 'active'
                
                # Retrieve subscription to calculate gb_extra and update plan immediately
                if subscription_id:
                    sub = stripe.Subscription.retrieve(subscription_id)
                    items_obj = getattr(sub, 'items', None)
                    items = getattr(items_obj, 'data', []) if items_obj else []
                    total_gb_extra = 0
                    
                    PRICE_10GB = getattr(settings, 'STRIPE_PRICE_10GB', '')
                    PRICE_50GB = getattr(settings, 'STRIPE_PRICE_50GB', '')
                    PRICE_BOUTIQUE = getattr(settings, 'STRIPE_PRICE_BOUTIQUE', '')
                    PRICE_CORPORATE = getattr(settings, 'STRIPE_PRICE_CORPORATE', '')
                    
                    for item in items:
                        price_obj = getattr(item, 'price', None)
                        p_id = getattr(price_obj, 'id', None) if price_obj else None
                        qty = getattr(item, 'quantity', 1)
                        if p_id == PRICE_10GB:
                            total_gb_extra += (10 * qty)
                        elif p_id == PRICE_50GB:
                            total_gb_extra += (50 * qty)
                        elif p_id == PRICE_CORPORATE:
                            tenant.plano_ativo = 'corporate'
                        elif p_id == PRICE_BOUTIQUE:
                            tenant.plano_ativo = 'boutique'
                            
                    # Note: Since Stripe allows multiple subscriptions per customer, 
                    # a robust implementation would sum across ALL active subscriptions.
                    # But for now, we sum the items in this specific session.
                    tenant.gb_extra += total_gb_extra
                
                tenant.save()
            except Client.DoesNotExist:
                pass
                
    elif event.type in ['customer.subscription.updated', 'customer.subscription.deleted']:
        subscription = event.data.object
        customer_id = getattr(subscription, 'customer', None)
        status = getattr(subscription, 'status', None)
        
        try:
            tenant = Client.objects.get(stripe_customer_id=customer_id)
            tenant.status_assinatura = status
            
            if status == 'canceled' or event.type == 'customer.subscription.deleted':
                tenant.gb_extra = 0
            else:
                items_obj = getattr(subscription, 'items', None)
                items = getattr(items_obj, 'data', []) if items_obj else []
                total_gb_extra = 0
                
                # These IDs will be configured via ENV later
                PRICE_10GB = getattr(settings, 'STRIPE_PRICE_10GB', '')
                PRICE_50GB = getattr(settings, 'STRIPE_PRICE_50GB', '')
                PRICE_BOUTIQUE = getattr(settings, 'STRIPE_PRICE_BOUTIQUE', '')
                PRICE_CORPORATE = getattr(settings, 'STRIPE_PRICE_CORPORATE', '')
                
                for item in items:
                    price_obj = getattr(item, 'price', None)
                    p_id = getattr(price_obj, 'id', None) if price_obj else None
                    qty = getattr(item, 'quantity', 1)
                    
                    if p_id == PRICE_10GB:
                        total_gb_extra += (10 * qty)
                    elif p_id == PRICE_50GB:
                        total_gb_extra += (50 * qty)
                    elif p_id == PRICE_CORPORATE:
                        tenant.plano_ativo = 'corporate'
                    elif p_id == PRICE_BOUTIQUE:
                        tenant.plano_ativo = 'boutique'
                        
                tenant.gb_extra = total_gb_extra
                
            tenant.save()
        except Client.DoesNotExist:
            pass

    return HttpResponse(status=200)

@login_required
def upgrade_plan(request):
    """
    Custom endpoint to upgrade the base plan directly via API, bypassing the Stripe Portal.
    """
    tenant = request.tenant
    
    if not tenant.stripe_customer_id:
        return redirect('core:assinatura')
        
    try:
        # 1. Fetch all active subscriptions for this customer
        subs = stripe.Subscription.list(customer=tenant.stripe_customer_id, status='all')
        
        PRICE_BOUTIQUE = getattr(settings, 'STRIPE_PRICE_BOUTIQUE', '')
        PRICE_CORPORATE = getattr(settings, 'STRIPE_PRICE_CORPORATE', '')
        
        target_sub = None
        target_item_id = None
        
        # 2. Find which subscription is the Base Plan (Boutique)
        all_subs = list(subs.auto_paging_iter())
        
        print(f"DEBUG upgrade_plan: Found {len(all_subs)} subscriptions for customer {tenant.stripe_customer_id}")
        
        for sub in all_subs:
            print(f"DEBUG upgrade_plan: checking sub {sub.id}")
            if hasattr(sub, 'items') and hasattr(sub.items, 'data'):
                for item in sub.items.data:
                    price_id = item.price.id if hasattr(item, 'price') and hasattr(item.price, 'id') else None
                    print(f"DEBUG upgrade_plan: item {item.id}, price_id {price_id} vs {PRICE_BOUTIQUE} / {PRICE_CORPORATE}")
                    if price_id in [PRICE_BOUTIQUE, PRICE_CORPORATE]:
                        target_sub = sub
                        target_item_id = item.id
                        break
            if target_sub:
                break
                
        if target_sub and target_item_id:
            # 3. Modify the subscription in Stripe (Swap Boutique for Corporate)
            # Stripe automatically prorates the charge based on unused time!
            stripe.Subscription.modify(
                target_sub.id,
                items=[{
                    'id': target_item_id,
                    'price': PRICE_CORPORATE, # The new price
                }],
                proration_behavior='create_prorations',
            )
            
            # 4. Update local DB immediately for better UX
            tenant.plano_ativo = 'corporate'
            tenant.save()
            from django.contrib import messages
            messages.success(request, 'Upgrade realizado com sucesso!')
        else:
            if tenant.plano_ativo == 'boutique':
                pass
            
            # DEBUG: collect what we saw
            seen_prices = []
            for sub in all_subs:
                if hasattr(sub, 'items') and hasattr(sub.items, 'data'):
                    for item in sub.items.data:
                        pid = item.price.id if hasattr(item, 'price') and hasattr(item.price, 'id') else str(getattr(item, 'price', 'none'))
                        seen_prices.append(pid)
                        
            from django.contrib import messages
            msg = f'Não foi possível encontrar a assinatura base no Stripe para realizar o upgrade. Esperado: {PRICE_BOUTIQUE}. Vistos: {", ".join(seen_prices)}'
            messages.warning(request, msg)
            
    except Exception as e:
        print(f"Erro no Upgrade: {str(e)}")
        from django.contrib import messages
        messages.error(request, f"Erro no Upgrade: {str(e)}")
        
    return redirect('core:assinatura')

@login_required
def downgrade_plan(request):
    """
    Custom endpoint to downgrade from Corporate to Boutique.
    """
    tenant = request.tenant
    
    if not tenant.stripe_customer_id:
        return redirect('core:assinatura')
        
    try:
        subs = stripe.Subscription.list(customer=tenant.stripe_customer_id, status='all')
        
        PRICE_BOUTIQUE = getattr(settings, 'STRIPE_PRICE_BOUTIQUE', '')
        PRICE_CORPORATE = getattr(settings, 'STRIPE_PRICE_CORPORATE', '')
        
        target_sub = None
        target_item_id = None
        
        for sub in subs.auto_paging_iter():
            if hasattr(sub, 'items') and hasattr(sub.items, 'data'):
                for item in sub.items.data:
                    price_id = item.price.id if hasattr(item, 'price') and hasattr(item.price, 'id') else None
                    if price_id == PRICE_CORPORATE:
                        target_sub = sub
                        target_item_id = item.id
                        break
            if target_sub:
                break
                
        if target_sub and target_item_id:
            stripe.Subscription.modify(
                target_sub.id,
                items=[{
                    'id': target_item_id,
                    'price': PRICE_BOUTIQUE,
                }],
                proration_behavior='create_prorations',
            )
            tenant.plano_ativo = 'boutique'
            tenant.save()
            from django.contrib import messages
            messages.success(request, 'Downgrade realizado com sucesso!')
        else:
            # Fix desync: If they don't have corporate in Stripe but local is corporate, force local to boutique
            if tenant.plano_ativo == 'corporate':
                tenant.plano_ativo = 'boutique'
                tenant.save()
            from django.contrib import messages
            messages.warning(request, 'O seu plano já estava como Boutique no Stripe. Sincronizamos o sistema.')
            
    except Exception as e:
        print(f"Erro no Downgrade: {str(e)}")
        from django.contrib import messages
        messages.error(request, f"Erro no Downgrade: {str(e)}")
        
    return redirect('core:assinatura')

@login_required
def cancel_plan(request):
    """
    Custom endpoint to cancel the base plan directly via API.
    """
    tenant = request.tenant
    
    if not tenant.stripe_customer_id:
        return redirect('core:assinatura')
        
    if request.method == 'GET':
        return render(request, 'core/crm/cancelar_assinatura.html')
        
    try:
        # 1. Fetch all active subscriptions for this customer
        subs = stripe.Subscription.list(customer=tenant.stripe_customer_id, status='all')
        
        canceled_any = False
        for sub in subs.auto_paging_iter():
            stripe.Subscription.modify(sub.id, cancel_at_period_end=True)
            canceled_any = True
            
        from django.contrib import messages
        if canceled_any:
            # We keep their current plan active, but mark it as canceling
            tenant.status_assinatura = 'canceling'
            tenant.save()
            messages.success(request, 'Sua assinatura foi programada para cancelamento. Você poderá continuar utilizando todos os recursos Premium até o fim do ciclo já pago. Sentiremos sua falta!')
        else:
            tenant.status_assinatura = 'canceled'
            tenant.plano_ativo = 'free'
            tenant.save()
            messages.success(request, 'Seu plano foi redefinido para a versão gratuita. Sentiremos sua falta!')
            
    except Exception as e:
        print(f"Erro no Cancelamento: {str(e)}")
        from django.contrib import messages
        messages.error(request, f"Erro no Cancelamento: {str(e)}")
        
    return redirect('core:assinatura')

@login_required
def update_card(request):
    tenant = request.tenant
    
    if not tenant.stripe_customer_id:
        return redirect('core:assinatura')
        
    try:
        intent = stripe.SetupIntent.create(
            customer=tenant.stripe_customer_id,
            payment_method_types=['card'],
            usage='off_session',
        )
        
        context = {
            'client_secret': intent.client_secret,
            'stripe_public_key': getattr(settings, 'STRIPE_PUBLISHABLE_KEY', '')
        }
        return render(request, 'core/crm/atualizar_cartao.html', context)
        
    except Exception as e:
        print(f"Erro ao gerar SetupIntent: {str(e)}")
        from django.contrib import messages
        messages.error(request, "Erro ao acessar o sistema de pagamento.")
        return redirect('core:assinatura')

@login_required
def faturamento_view(request):
    """
    Renders a custom HTML page showing the billing history from Stripe.
    """
    tenant = request.tenant
    
    invoices_data = []
    
    if tenant.stripe_customer_id:
        try:
            # Fetch all invoices for the customer
            invoices = stripe.Invoice.list(customer=tenant.stripe_customer_id, limit=100)
            
            for inv in invoices.auto_paging_iter():
                from datetime import datetime
                # Format date
                date_str = datetime.fromtimestamp(inv.created).strftime('%d/%m/%Y')
                
                # Get lines descriptions
                linhas = []
                for line in getattr(getattr(inv, 'lines', None), 'data', []):
                    desc = getattr(line, 'description', '')
                    if desc:
                        import re
                        # Remove "(at R$ X.XX / month)" or "(a R$ X.XX / month)"
                        desc = re.sub(r'\s*\((a|at)\s*R\$.*?\)', '', desc)
                        linhas.append(desc)
                
                # Format amount
                valor = getattr(inv, 'amount_paid', 0)
                if not valor and getattr(inv, 'status') != 'paid':
                    valor = getattr(inv, 'amount_due', 0)
                    
                valor_str = f"R$ {valor / 100:.2f}".replace('.', ',')
                
                invoices_data.append({
                    'data': date_str,
                    'linhas': linhas,
                    'status': getattr(inv, 'status', 'unknown'),
                    'valor': valor_str,
                    'url_recibo': getattr(inv, 'hosted_invoice_url', '')
                })
        except Exception as e:
            logger.error(f"Error fetching invoices for faturamento view: {str(e)}")
            
    context = {
        'invoices': invoices_data,
        'tenant': tenant
    }
    from django.shortcuts import render
    return render(request, 'core/crm/faturamento.html', context)
