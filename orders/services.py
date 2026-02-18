from django.db import transaction
from .models import Order, OrderItem
from cart.models import Cart, CartItem
from products.models import Product
from core.exceptions import CartEmptyException


def create_order_from_cart(user, shipping_address='', phone_number='', notes=''):

    with transaction.atomic():

        cart = Cart.objects.filter(user=user).first()
        if not cart or not cart.items.filter(is_active=True).exists():
            raise CartEmptyException()


        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            phone_number=phone_number,
            notes=notes,
            status='new'
        )

        total_price = 0
        cart_items = cart.items.filter(is_active=True)

        for cart_item in cart_items:
            product = cart_item.product

            if product.quantity < cart_item.quantity:
                order.delete()
                raise ValueError(
                    f"{product.title} mahsulotidan faqat {product.quantity} ta qolgan"
                )

            product.quantity -= cart_item.quantity
            product.save()

            OrderItem.objects.create(
                order=order,
                product=product,
                price=product.price,
                quantity=cart_item.quantity
            )

            total_price += product.price * cart_item.quantity

            cart_item.is_active = False
            cart_item.save()

        order.total_price = total_price
        order.save()

        cart.calculate_total()

        return order


def calculate_order_total(order):

    total = sum(item.total_price for item in order.items.all())
    order.total_price = total
    order.save()
    return total