from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from shared.models import BaseModel
from users.models import User
from products.models import Product


class Comment(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'product']  # Har bir user faqat bir marta comment qoldirishi mumkin

    def __str__(self):
        return f"Comment by {self.user.username} on {self.product.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)


        if is_new:
            self.update_product_rating()

    def update_product_rating(self):
        product = self.product
        comments = product.comments.filter(is_active=True)

        if comments.exists():
            total_rating = sum(comment.rating for comment in comments)
            avg_rating = total_rating / comments.count()
            product.rating = round(avg_rating, 1)
            product.total_ratings = comments.count()
            product.save()