from django.db import models
from django.core.validators import MinValueValidator
from shared.models import BaseModel
from categories.models import Category
from django.utils.text import slugify

class Product(BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2,
                               validators=[MinValueValidator(0)])
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                               related_name='products')
    is_active = models.BooleanField(default=True)
    rating = models.FloatField(default=0.0)
    total_ratings = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def in_stock(self):
        return self.quantity > 0

    @property
    def main_image(self):
        main = self.images.filter(is_main=True).first()
        if main:
            return main.image.url
        return None

class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                               related_name='images')
    image = models.ImageField(upload_to='products/')
    is_main = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_main', 'created_at']

    def __str__(self):
        return f"Image for {self.product.title}"