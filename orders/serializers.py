from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer
from users.serializers import UserProfileSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'price', 'quantity', 'total_price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserProfileSerializer(read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_price', 'status', 'status_display',
                 'shipping_address', 'phone_number', 'notes', 'items',
                 'can_cancel', 'is_completed', 'created_at', 'updated_at']
        read_only_fields = ['user', 'total_price', 'created_at', 'updated_at']

class CreateOrderSerializer(serializers.Serializer):
    shipping_address = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)
    notes = serializers.CharField(required=False)

class UpdateOrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['paid', 'shipped', 'delivered', 'cancelled'])