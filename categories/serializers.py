from rest_framework import serializers
from .models import Category

class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'title', 'slug', 'parent', 'is_active',
                 'children', 'product_count', 'created_at', 'updated_at']
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def get_children(self, obj):
        children = obj.get_children
        if children:
            return CategorySerializer(children, many=True).data
        return []

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['title', 'parent', 'is_active']