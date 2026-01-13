from django.db import models
from django.core.validators import MinValueValidator
from shared.models import BaseModel
from users.models import User
from products.models import Product

class Cart(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                               related_name='cart')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Cart of {self.user.username}"

    def calculate_total(self):
        total = sum(item.total_price for item in self.items.filter(is_active=True))
        self.total_price = total
        self.save()
        return total

    @property
    def item_count(self):
        return self.items.filter(is_active=True).count()

class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE,
                            related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1,
                                  validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

    @property
    def total_price(self):
        return self.product.price * self.quantity

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.cart.calculate_total()