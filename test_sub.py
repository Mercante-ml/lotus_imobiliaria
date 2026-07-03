import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

from django.conf import settings
from clientes.models import Client
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

tenant = Client.objects.first()
PRICE_BOUTIQUE = getattr(settings, 'STRIPE_PRICE_BOUTIQUE', '')
PRICE_CORPORATE = getattr(settings, 'STRIPE_PRICE_CORPORATE', '')

print(f"Boutique price: {PRICE_BOUTIQUE}")
print(f"Corporate price: {PRICE_CORPORATE}")

subs = stripe.Subscription.list(customer=tenant.stripe_customer_id, status='all')
target_sub = None
target_item_id = None

for sub in subs.auto_paging_iter():
    for item in sub.items.data:
        price_id = item.price.id if hasattr(item, 'price') and hasattr(item.price, 'id') else None
        print(f"Comparing '{price_id}' with '{PRICE_BOUTIQUE}' and '{PRICE_CORPORATE}'")
        if price_id in [PRICE_BOUTIQUE, PRICE_CORPORATE]:
            target_sub = sub
            target_item_id = item.id
            break
    if target_sub:
        break

print(f"Target sub found: {target_sub is not None}")
