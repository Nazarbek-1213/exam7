from rest_framework import generics, permissions, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from .models import *
from .serializers import *
from products.models import Product
from core.permissions import IsOwnerOrAdmin

class ProductCommentsListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['rating', 'created_at']

    def get_queryset(self):
        product_slug = self.kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        return Comment.objects.filter(product=product, is_active=True)

class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        product_slug = self.kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        serializer.save(user=self.request.user, product=product)

class CommentUpdateView(generics.UpdateAPIView):
    queryset = Comment.objects.filter(is_active=True)
    serializer_class = CommentUpdateSerializer
    permission_classes = [IsOwnerOrAdmin]
    lookup_field = 'id'

class CommentDeleteView(generics.DestroyAPIView):
    queryset = Comment.objects.filter(is_active=True)
    permission_classes = [IsOwnerOrAdmin]
    lookup_field = 'id'

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

class AllCommentsListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['text', 'product__title']
    ordering_fields = ['created_at', 'rating']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Comment.objects.filter(is_active=True)
        return Comment.objects.filter(user=user, is_active=True)