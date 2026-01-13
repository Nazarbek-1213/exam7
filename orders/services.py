from django.db import transaction
from .models import Order, OrderItem
from cart.models import Cart, CartItem
from products.models import Product
from core.exceptions import CartEmptyException


def create_order_from_cart(user, shipping_address='', phone_number='', notes=''):
    """
    Foydalanuvchi savatidan buyurtma yaratish
    """
    with transaction.atomic():
        # 1. Savatni olish
        cart = Cart.objects.filter(user=user).first()
        if not cart or not cart.items.filter(is_active=True).exists():
            raise CartEmptyException()

        # 2. Buyurtma yaratish
        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            phone_number=phone_number,
            notes=notes,
            status='new'
        )

        # 3. Savatdagi mahsulotlarni buyurtma itemlariga aylantirish
        total_price = 0
        cart_items = cart.items.filter(is_active=True)

        for cart_item in cart_items:
            product = cart_item.product

            # Mahsulot miqdori yetarli ekanligini tekshirish
            if product.quantity < cart_item.quantity:
                order.delete()
                raise ValueError(
                    f"{product.title} mahsulotidan faqat {product.quantity} ta qolgan"
                )

            # Mahsulot miqdorini kamaytirish
            product.quantity -= cart_item.quantity
            product.save()

            # OrderItem yaratish
            OrderItem.objects.create(
                order=order,
                product=product,
                price=product.price,
                quantity=cart_item.quantity
            )

            total_price += product.price * cart_item.quantity

            # Savat item'ini deaktiv qilish
            cart_item.is_active = False
            cart_item.save()

        # 4. Buyurtma umumiy narxini yangilash
        order.total_price = total_price
        order.save()

        # 5. Savat umumiy narxini yangilash
        cart.calculate_total()

        return order


def calculate_order_total(order):
    """
    Buyurtma umumiy narxini hisoblash
    """
    total = sum(item.total_price for item in order.items.all())
    order.total_price = total
    order.save()
    return total