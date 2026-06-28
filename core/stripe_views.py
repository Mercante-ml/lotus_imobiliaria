import stripe
import logging
from django.conf import settings
from django.shortcuts import redirect
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
        subs = stripe.Subscription.list(customer=tenant.stripe_customer_id, status='active')
        
        PRICE_BOUTIQUE = getattr(settings, 'STRIPE_PRICE_BOUTIQUE', '')
        PRICE_CORPORATE = getattr(settings, 'STRIPE_PRICE_CORPORATE', '')
        
        target_sub = None
        target_item_id = None
        
        # 2. Find which subscription is the Base Plan (Boutique)
        for sub in subs.auto_paging_iter():
            for item in getattr(getattr(sub, 'items', None), 'data', []):
                price_id = getattr(getattr(item, 'price', None), 'id', None)
                if price_id in [PRICE_BOUTIQUE, PRICE_CORPORATE]:
                    target_sub = sub
                    target_item_id = getattr(item, 'id', None)
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
            
    except Exception as e:
        print(f"Erro no Upgrade: {str(e)}")
        
    return redirect('/crm/assinatura/?upgrade=success')

@login_required
def downgrade_plan(request):
    """
    Custom endpoint to downgrade from Corporate to Boutique.
    """
    tenant = request.tenant
    
    if not tenant.stripe_customer_id:
        return redirect('core:assinatura')
        
    try:
        subs = stripe.Subscription.list(customer=tenant.stripe_customer_id, status='active')
        
        PRICE_BOUTIQUE = getattr(settings, 'STRIPE_PRICE_BOUTIQUE', '')
        PRICE_CORPORATE = getattr(settings, 'STRIPE_PRICE_CORPORATE', '')
        
        target_sub = None
        target_item_id = None
        
        for sub in subs.auto_paging_iter():
            for item in getattr(getattr(sub, 'items', None), 'data', []):
                price_id = getattr(getattr(item, 'price', None), 'id', None)
                if price_id == PRICE_CORPORATE:
                    target_sub = sub
                    target_item_id = getattr(item, 'id', None)
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
            
    except Exception as e:
        print(f"Erro no Downgrade: {str(e)}")
        
    return redirect('/crm/assinatura/?downgrade=success')

@login_required
def cancel_plan(request):
    """
    Custom endpoint to cancel the base plan directly via API.
    """
    tenant = request.tenant
    
    if not tenant.stripe_customer_id:
        return redirect('core:assinatura')
        
    try:
        subs = stripe.Subscription.list(customer=tenant.stripe_customer_id, status='active')
        
        PRICE_BOUTIQUE = getattr(settings, 'STRIPE_PRICE_BOUTIQUE', '')
        PRICE_CORPORATE = getattr(settings, 'STRIPE_PRICE_CORPORATE', '')
        
        target_sub = None
        for sub in subs.auto_paging_iter():
            for item in getattr(getattr(sub, 'items', None), 'data', []):
                price_id = getattr(getattr(item, 'price', None), 'id', None)
                if price_id in [PRICE_BOUTIQUE, PRICE_CORPORATE]:
                    target_sub = sub
                    break
            if target_sub:
                break
                
        if target_sub:
            stripe.Subscription.delete(target_sub.id)
            tenant.status_assinatura = 'canceled'
            tenant.save()
            
    except Exception as e:
        print(f"Erro no Cancelamento: {str(e)}")
        
    return redirect('/crm/assinatura/?cancel=success')
