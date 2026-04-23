from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from .models import (
    ActivityLog,
    Cart,
    CartItem,
    Category,
    CustomerProfile,
    InventoryLog,
    Order,
    OrderItem,
    Payment,
    ProducerProfile,
    ProducerSubOrder,
    Product,
    RecommendationLog,
    Settlement,
    UserInteraction,
)
from .services.food_miles import postcode_distance_miles


COMMON_ALLERGEN_DEFAULT = 'No common allergens declared.'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class BaseRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Username already exists.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Email already exists.')
        return value

    def validate_password(self, value):
        if value.isdigit() or value.isalpha() or value.lower() == value or not any(ch.isdigit() for ch in value):
            raise serializers.ValidationError('Password must contain letters and numbers, and should not be all lowercase.')
        return value


class ProducerRegisterSerializer(BaseRegistrationSerializer):
    business_name = serializers.CharField()
    contact_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    business_address = serializers.CharField(required=False, allow_blank=True)
    postcode = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        producer = ProducerProfile.objects.create(
            user=user,
            business_name=validated_data['business_name'],
            contact_name=validated_data.get('contact_name', ''),
            phone=validated_data.get('phone', ''),
            business_address=validated_data.get('business_address', ''),
            postcode=validated_data.get('postcode', '').upper().strip(),
        )
        ActivityLog.objects.create(action='producer_registered', details=producer.business_name, user=user)
        return producer

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'business_name': instance.business_name,
            'user': UserSerializer(instance.user).data,
            'role': 'producer',
        }


class CustomerRegisterSerializer(BaseRegistrationSerializer):
    phone = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField()
    postcode = serializers.CharField()
    organisation_name = serializers.CharField(required=False, allow_blank=True)
    segment = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        customer = CustomerProfile.objects.create(
            user=user,
            phone=validated_data.get('phone', ''),
            address=validated_data['address'],
            postcode=validated_data['postcode'].upper().strip(),
            organisation_name=validated_data.get('organisation_name', ''),
            segment=validated_data.get('segment', 'household') or 'household',
        )
        Cart.objects.get_or_create(customer=customer)
        ActivityLog.objects.create(action='customer_registered', details=customer.user.username, user=user)
        return customer

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'user': UserSerializer(instance.user).data,
            'address': instance.address,
            'postcode': instance.postcode,
            'role': 'customer',
        }


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Invalid username or password.')
        attrs['user'] = user
        return attrs

    def to_representation(self, instance):
        role = 'user'
        profile_id = None
        if hasattr(instance, 'producer_profile'):
            role = 'producer'
            profile_id = instance.producer_profile.id
        elif hasattr(instance, 'customer_profile'):
            role = 'customer'
            profile_id = instance.customer_profile.id
        elif instance.is_staff or instance.is_superuser:
            role = 'admin'
        return {
            'user': UserSerializer(instance).data,
            'role': role,
            'profile_id': profile_id,
            'is_staff': instance.is_staff,
        }


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class ProductSerializer(serializers.ModelSerializer):
    current_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    producer_name = serializers.CharField(source='producer.business_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_visible = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'producer', 'producer_name', 'category', 'category_name', 'name', 'description',
            'price', 'current_price', 'unit', 'stock_quantity', 'availability', 'is_visible', 'harvest_date',
            'farm_origin', 'organic_certified', 'allergen_info', 'best_before', 'grade', 'discount_percent'
        ]

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError('Stock cannot be negative.')
        return value

    def validate_discount_percent(self, value):
        if value < 0 or value > 90:
            raise serializers.ValidationError('Discount percent must be between 0 and 90.')
        return value

    def validate(self, attrs):
        name = attrs.get('name') or getattr(self.instance, 'name', '')
        availability = attrs.get('availability') or getattr(self.instance, 'availability', 'available')
        stock_quantity = attrs.get('stock_quantity')
        if stock_quantity is None:
            stock_quantity = getattr(self.instance, 'stock_quantity', 0)
        if not name:
            raise serializers.ValidationError({'name': 'Product name is required.'})
        if availability in {'available', 'in_season'} and stock_quantity <= 0:
            raise serializers.ValidationError({'stock_quantity': 'Visible products must have stock greater than zero.'})
        if not attrs.get('allergen_info') and not getattr(self.instance, 'allergen_info', ''):
            attrs['allergen_info'] = COMMON_ALLERGEN_DEFAULT
        return attrs


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'line_total']

    def get_line_total(self, obj):
        return obj.line_total


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    grouped_by_producer = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'customer', 'items', 'grouped_by_producer', 'total']

    def get_total(self, obj):
        return obj.total

    def get_grouped_by_producer(self, obj):
        groups = {}
        for item in obj.items.select_related('product__producer').all():
            producer = item.product.producer
            bucket = groups.setdefault(
                str(producer.id),
                {
                    'producer_id': producer.id,
                    'producer_name': producer.business_name,
                    'items': [],
                    'subtotal': Decimal('0.00'),
                },
            )
            bucket['items'].append(CartItemSerializer(item).data)
            bucket['subtotal'] += item.line_total
        return list(groups.values())


class AddCartItemSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        customer = CustomerProfile.objects.get(pk=attrs['customer_id'])
        product = Product.objects.select_related('producer').get(pk=attrs['product_id'])
        if not product.is_visible:
            raise serializers.ValidationError('Product is not currently available.')
        if attrs['quantity'] > product.stock_quantity:
            raise serializers.ValidationError('Requested quantity exceeds available stock.')
        attrs['customer'] = customer
        attrs['product'] = product
        return attrs

    def save(self):
        customer = self.validated_data['customer']
        product = self.validated_data['product']
        cart, _ = Cart.objects.get_or_create(customer=customer)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': self.validated_data['quantity']})
        if not created:
            item.quantity += self.validated_data['quantity']
            if item.quantity > product.stock_quantity:
                raise serializers.ValidationError('Requested quantity exceeds available stock.')
            item.save(update_fields=['quantity'])
        UserInteraction.objects.create(customer=customer, product=product, interaction_type='add_to_cart')
        return item


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        item = self.context['item']
        if value > item.product.stock_quantity:
            raise serializers.ValidationError('Requested quantity exceeds available stock.')
        return value

    def update(self, instance, validated_data):
        instance.quantity = validated_data['quantity']
        instance.save(update_fields=['quantity'])
        return instance


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'item_total']


class ProducerSubOrderSerializer(serializers.ModelSerializer):
    producer_name = serializers.CharField(source='producer.business_name', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = ProducerSubOrder
        fields = ['id', 'producer', 'producer_name', 'status', 'subtotal', 'producer_payout', 'delivery_date', 'delivery_notes', 'items']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    suborders = ProducerSubOrderSerializer(many=True, read_only=True)
    transaction_reference = serializers.CharField(source='payment.transaction_reference', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'status', 'delivery_address', 'delivery_date', 'total_amount', 'commission_amount',
            'food_miles_total', 'payment_status', 'transaction_reference', 'items', 'suborders'
        ]


class OrderCreateSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    delivery_address = serializers.CharField(required=False, allow_blank=True)
    delivery_date = serializers.DateField(required=False)
    producer_delivery_dates = serializers.DictField(child=serializers.DateField(), required=False)
    payment_method = serializers.CharField(required=False, default='sandbox')
    simulate_payment_failure = serializers.BooleanField(required=False, default=False)

    @transaction.atomic
    def create(self, validated_data):
        customer = CustomerProfile.objects.select_related('cart').get(pk=validated_data['customer_id'])
        cart = customer.cart
        cart_items = list(cart.items.select_related('product__producer').all())
        if not cart_items:
            raise serializers.ValidationError('Cart is empty.')

        default_min_date = timezone.localdate() + timedelta(days=2)
        delivery_date = validated_data.get('delivery_date', default_min_date)
        if delivery_date < default_min_date:
            raise serializers.ValidationError('Delivery date must be at least 48 hours ahead.')

        if validated_data.get('simulate_payment_failure'):
            raise serializers.ValidationError('Payment failed in sandbox mode. Please retry with a valid test payment.')

        order = Order.objects.create(
            customer=customer,
            delivery_address=validated_data.get('delivery_address') or customer.address,
            delivery_date=delivery_date,
            payment_status='pending',
        )

        producer_delivery_dates = validated_data.get('producer_delivery_dates', {})
        grouped = {}
        total = Decimal('0.00')
        food_miles = Decimal('0.00')

        for cart_item in cart_items:
            product = cart_item.product
            producer = product.producer
            if cart_item.quantity > product.stock_quantity:
                raise serializers.ValidationError(f'Insufficient stock for {product.name}.')

            suborder = grouped.get(producer.id)
            if suborder is None:
                requested_date = producer_delivery_dates.get(str(producer.id)) or producer_delivery_dates.get(producer.id)
                producer_min_date = timezone.localdate() + timedelta(days=max(2, producer.lead_time_hours // 24))
                selected_date = requested_date or delivery_date
                if selected_date < producer_min_date:
                    raise serializers.ValidationError(f'Delivery date for {producer.business_name} must respect the 48-hour lead time.')
                suborder = ProducerSubOrder.objects.create(
                    order=order,
                    producer=producer,
                    delivery_date=selected_date,
                )
                grouped[producer.id] = suborder

            line_total = (product.current_price * cart_item.quantity).quantize(Decimal('0.01'))
            OrderItem.objects.create(
                order=order,
                suborder=suborder,
                product=product,
                quantity=cart_item.quantity,
                unit_price=product.current_price,
                item_total=line_total,
            )
            suborder.subtotal += line_total
            distance = Decimal(str(postcode_distance_miles(customer.postcode, producer.postcode)))
            food_miles += distance * cart_item.quantity
            total += line_total
            previous_stock = product.stock_quantity
            product.stock_quantity -= cart_item.quantity
            if product.stock_quantity == 0:
                product.availability = 'unavailable'
                product.save(update_fields=['stock_quantity', 'availability'])
            else:
                product.save(update_fields=['stock_quantity'])
            InventoryLog.objects.create(product=product, previous_stock=previous_stock, new_stock=product.stock_quantity, note='Order placed')
            UserInteraction.objects.create(customer=customer, product=product, interaction_type='purchase')

        commission = (total * Decimal('0.05')).quantize(Decimal('0.01'))
        for suborder in grouped.values():
            suborder.producer_payout = (suborder.subtotal * Decimal('0.95')).quantize(Decimal('0.01'))
            suborder.save(update_fields=['subtotal', 'producer_payout', 'delivery_date'])

        order.total_amount = total
        order.commission_amount = commission
        order.food_miles_total = food_miles.quantize(Decimal('0.01'))
        order.payment_status = 'succeeded'
        order.save(update_fields=['total_amount', 'commission_amount', 'food_miles_total', 'payment_status'])
        Payment.objects.create(
            order=order,
            provider=validated_data.get('payment_method', 'sandbox'),
            transaction_reference=f'TEST-{uuid4().hex[:12].upper()}',
            amount=total,
            status='succeeded',
        )
        cart.items.all().delete()
        ActivityLog.objects.create(action='order_created', details=f'Created order {order.id}', user=customer.user)
        return order


class UpdateSubOrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['pending', 'confirmed', 'ready', 'delivered'])
    delivery_notes = serializers.CharField(required=False, allow_blank=True)

    def validate_status(self, value):
        instance = self.instance
        allowed_next = {
            'pending': {'confirmed'},
            'confirmed': {'ready'},
            'ready': {'delivered'},
            'delivered': set(),
        }
        current = instance.status
        if value != current and value not in allowed_next[current]:
            raise serializers.ValidationError(f'Status must progress in order. Current status: {current}.')
        return value

    def update(self, instance, validated_data):
        instance.status = validated_data['status']
        instance.delivery_notes = validated_data.get('delivery_notes', instance.delivery_notes)
        instance.save(update_fields=['status', 'delivery_notes'])

        all_statuses = set(instance.order.suborders.values_list('status', flat=True))
        if all_statuses == {'delivered'}:
            instance.order.status = 'delivered'
        elif 'ready' in all_statuses and all_statuses.issubset({'ready', 'delivered'}):
            instance.order.status = 'ready'
        elif 'confirmed' in all_statuses and all_statuses.issubset({'confirmed', 'ready', 'delivered'}):
            instance.order.status = 'confirmed'
        else:
            instance.order.status = 'pending'
        instance.order.save(update_fields=['status'])
        return instance


class SettlementSerializer(serializers.ModelSerializer):
    running_tax_year_total = serializers.SerializerMethodField()

    class Meta:
        model = Settlement
        fields = ['id', 'producer', 'week_start', 'week_end', 'orders_total', 'commission_total', 'payout_total', 'status', 'running_tax_year_total']

    def get_running_tax_year_total(self, obj):
        start = obj.week_start.replace(month=1, day=1)
        total = Settlement.objects.filter(producer=obj.producer, week_start__gte=start).aggregate(total=Sum('payout_total'))
        return total['total'] or Decimal('0.00')
