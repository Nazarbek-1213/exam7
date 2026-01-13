from rest_framework import serializers

from categories.models import Category
from .models import Product, ProductImage
from categories.serializers import CategorySerializer

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_main']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source='category',
        write_only=True
    )
    images = ProductImageSerializer(many=True, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    main_image = serializers.SerializerMethodField()
    total_comments = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'description', 'price',
                 'quantity', 'category', 'category_id', 'is_active',
                 'rating', 'in_stock', 'images', 'main_image',
                 'total_comments', 'created_at', 'updated_at']
        read_only_fields = ['slug', 'rating', 'total_ratings']

    def get_main_image(self, obj):
        return obj.main_image

    def get_total_comments(self, obj):
        return obj.comments.filter(is_active=True).count()

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'quantity',
                 'category', 'is_active']

class ProductSearchSerializer(serializers.Serializer):
    q = serializers.CharField(required=False)
    category = serializers.CharField(required=False)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    in_stock = serializers.BooleanField(required=False)