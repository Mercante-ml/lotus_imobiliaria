from django.contrib.auth.models import User

# Cria o superusuário no schema public (onde a tabela auth_user reside, já que é SHARED_APP)
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@dsprime.com', 'Lotus123!')
    print("Superusuário criado: admin / Lotus123!")
else:
    print("Superusuário 'admin' já existe.")
