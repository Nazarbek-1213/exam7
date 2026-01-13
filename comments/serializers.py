from rest_framework import serializers
from .models import Comment
from users.serializers import UserProfileSerializer


class CommentSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    product_title = serializers.CharField(source='product.title', read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'product', 'product_title', 'text',
                  'rating', 'is_active', 'can_edit', 'created_at', 'updated_at']
        read_only_fields = ['user', 'product', 'created_at', 'updated_at']

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.user == request.user or request.user.is_staff
        return False

    def validate(self, data):
        # Faqat bir marta comment qoldirishni tekshirish
        request = self.context.get('request')
        product = self.instance.product if self.instance else data.get('product')

        if request and product and not self.instance:
            existing_comment = Comment.objects.filter(
                user=request.user,
                product=product,
                is_active=True
            ).exists()
            if existing_comment:
                raise serializers.ValidationError(
                    "Siz bu mahsulotga allaqachon izoh qoldirgansiz"
                )
        return data


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['product', 'text', 'rating']


class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['text', 'rating']