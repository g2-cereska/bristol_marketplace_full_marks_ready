from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from marketplace.models import Cart, Category, CustomerProfile, ProducerProfile, Product


class Command(BaseCommand):
    help = 'Seeds demo data for the Bristol marketplace project.'

    def handle(self, *args, **options):
        veg, _ = Category.objects.get_or_create(name='Vegetables', slug='vegetables')
        dairy, _ = Category.objects.get_or_create(name='Dairy Products', slug='dairy-products')
        bakery, _ = Category.objects.get_or_create(name='Bakery Goods', slug='bakery-goods')

        p1_user, created = User.objects.get_or_create(username='producer_jane', defaults={'email': 'jane@example.com'})
        p1_user.set_password('Password123!')
        p1_user.save()
        p1, _ = ProducerProfile.objects.get_or_create(user=p1_user, defaults={'business_name': 'Bristol Valley Farm', 'postcode': 'BS1 4DJ'})
        p2_user, _ = User.objects.get_or_create(username='producer_dairy', defaults={'email': 'dairy@example.com'})
        p2_user.set_password('Password123!')
        p2_user.save()
        p2, _ = ProducerProfile.objects.get_or_create(user=p2_user, defaults={'business_name': 'Hillside Dairy', 'postcode': 'BS5 8AA'})

        c_user, _ = User.objects.get_or_create(username='customer_robert', defaults={'email': 'robert@example.com'})
        c_user.set_password('Password123!')
        c_user.save()
        customer, _ = CustomerProfile.objects.get_or_create(
            user=c_user,
            defaults={'address': '45 Park Street, Bristol', 'postcode': 'BS1 5JG', 'segment': 'family'}
        )
        Cart.objects.get_or_create(customer=customer)

        products = [
            dict(producer=p1, category=veg, name='Organic Tomatoes', description='Fresh local tomatoes', price=Decimal('3.20'), stock_quantity=40, availability='in_season', organic_certified=True, farm_origin='Bristol Valley Farm', harvest_date=date.today(), best_before=date.today() + timedelta(days=5)),
            dict(producer=p1, category=veg, name='Organic Carrots', description='Crunchy carrots', price=Decimal('2.50'), stock_quantity=35, availability='available', organic_certified=True, farm_origin='Bristol Valley Farm', harvest_date=date.today(), best_before=date.today() + timedelta(days=6)),
            dict(producer=p2, category=dairy, name='Fresh Milk', description='1 litre whole milk', price=Decimal('1.80'), stock_quantity=50, availability='available', allergen_info='Contains milk', farm_origin='Hillside Dairy', best_before=date.today() + timedelta(days=4)),
            dict(producer=p2, category=bakery, name='Farm Bread', description='Rustic loaf', price=Decimal('2.90'), stock_quantity=22, availability='available', farm_origin='Hillside Dairy', best_before=date.today() + timedelta(days=2), discount_percent=10),
        ]
        for product_data in products:
            Product.objects.get_or_create(name=product_data['name'], producer=product_data['producer'], defaults=product_data)

        # Admin superuser — accessible at /market/admin-dash/
        admin_user, _ = User.objects.get_or_create(
            username='admin_1',
            defaults={'email': 'admin@bristol-food.example.com', 'is_staff': True, 'is_superuser': True}
        )
        admin_user.set_password('Password123!')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        self.stdout.write(self.style.SUCCESS('Demo data created/updated successfully.'))