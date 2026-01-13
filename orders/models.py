from django.db import models
from django.core.validators import MinValueValidator
from shared.models import BaseModel
from users.models import User
from products.models import Product

ORDER_STATUS = (
    ('new', 'Yangi'),
    ('paid', "To'langan"),
    ('shipped', 'Yuborilgan'),
    ('delivered', 'Yetkazilgan'),
    ('cancelled', 'Bekor qilingan'),
)

class Order(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='new')
    shipping_address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

    @property
    def can_cancel(self):
        return self.status in ['new', 'paid']

    @property
    def is_completed(self):
        return self.status == 'delivered'

class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.quantity} x {self.product.title if self.product else 'Deleted Product'}"

    @property
    def total_price(self):
        return self.price * self.quantity