from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializers import (CartSerializer, CartItemSerializer,
                          AddToCartSerializer, UpdateCartItemSerializer)
from products.models import Product
from core.exceptions import CartEmptyException


class CartDetailView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart


class AddToCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']

        product = get_object_or_404(Product, id=product_id, is_active=True)

        if product.quantity < quantity:
            return Response({
                'error': f'Faqat {product.quantity} ta mahsulot qolgan'
            }, status=status.HTTP_400_BAD_REQUEST)

        cart, created = Cart.objects.get_or_create(user=request.user)

        # Check if product already in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'is_active': True}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.is_active = True
            cart_item.save()

        return Response({
            'message': 'Mahsulot savatga qoʻshildi',
            'cart_item': CartItemSerializer(cart_item).data
        }, status=status.HTTP_200_OK)


class RemoveFromCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({
                'error': 'product_id maydoni kerak'
            }, status=status.HTTP_400_BAD_REQUEST)

        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id, is_active=True)

        cart_item.is_active = False
        cart_item.save()

        return Response({
            'message': 'Mahsulot savatdan olib tashlandi'
        }, status=status.HTTP_200_OK)


class ClearCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.filter(is_active=True).update(is_active=False)
        cart.calculate_total()

        return Response({
            'message': 'Savat tozalandi'
        }, status=status.HTTP_200_OK)


class UpdateCartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = request.data.get('product_id')
        quantity = serializer.validated_data['quantity']

        if not product_id:
            return Response({
                'error': 'product_id maydoni kerak'
            }, status=status.HTTP_400_BAD_REQUEST)

        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id, is_active=True)

        product = cart_item.product
        if product.quantity < quantity:
            return Response({
                'error': f'Faqat {product.quantity} ta mahsulot qolgan'
            }, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = quantity
        cart_item.save()

        return Response({
            'message': 'Mahsulot miqdori yangilandi',
            'cart_item': CartItemSerializer(cart_item).data
        }, status=status.HTTP_200_OK)