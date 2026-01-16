#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from stores.models import Store
from products.models import Product

# Criar usuário de teste
user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@example.com',
        'is_staff': True,
        'is_superuser': True
    }
)
if created:
    user.set_password('admin123')
    user.save()
    print(f'✅ Usuário criado: admin / admin123')
else:
    print(f'ℹ️  Usuário já existe: admin')

# Criar lojas de teste
stores_data = [
    {'name': 'Loja Tech', 'slug': 'loja-tech', 'description': 'Produtos de tecnologia'},
    {'name': 'Moda Store', 'slug': 'moda-store', 'description': 'Roupas e acessórios'},
]

for store_data in stores_data:
    store, created = Store.objects.get_or_create(
        slug=store_data['slug'],
        defaults={
            'name': store_data['name'],
            'description': store_data['description'],
            'owner': user
        }
    )
    if created:
        print(f'✅ Loja criada: {store.name}')
    else:
        print(f'ℹ️  Loja já existe: {store.name}')

# Criar produtos de teste
loja_tech = Store.objects.get(slug='loja-tech')
moda_store = Store.objects.get(slug='moda-store')

products_data = [
    {'store': loja_tech, 'name': 'Notebook Dell', 'slug': 'notebook-dell', 'price': 3499.90, 'stock': 10},
    {'store': loja_tech, 'name': 'Mouse Logitech', 'slug': 'mouse-logitech', 'price': 89.90, 'stock': 50},
    {'store': loja_tech, 'name': 'Teclado Mecânico', 'slug': 'teclado-mecanico', 'price': 299.90, 'stock': 25},
    {'store': moda_store, 'name': 'Camiseta Básica', 'slug': 'camiseta-basica', 'price': 49.90, 'stock': 100},
    {'store': moda_store, 'name': 'Calça Jeans', 'slug': 'calca-jeans', 'price': 149.90, 'stock': 40},
    {'store': moda_store, 'name': 'Tênis Esportivo', 'slug': 'tenis-esportivo', 'price': 249.90, 'stock': 30},
]

for product_data in products_data:
    product, created = Product.objects.get_or_create(
        store=product_data['store'],
        slug=product_data['slug'],
        defaults={
            'name': product_data['name'],
            'price': product_data['price'],
            'stock': product_data['stock'],
            'description': f'Descrição do produto {product_data["name"]}'
        }
    )
    if created:
        print(f'✅ Produto criado: {product.name} ({product.store.name})')
    else:
        print(f'ℹ️  Produto já existe: {product.name}')

print('\n🎉 Dados de teste criados com sucesso!')
print('\n📝 Credenciais de acesso:')
print('   Usuário: admin')
print('   Senha: admin123')
