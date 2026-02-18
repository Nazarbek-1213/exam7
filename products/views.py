from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Product
from .serializers import *
from core.permissions import IsAdminOrReadOnly


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'rating', 'created_at']
    filterset_fields = ['category', 'is_active']

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category')

        # Filter by in_stock
        in_stock = self.request.query_params.get('in_stock')
        if in_stock is not None:
            if in_stock.lower() == 'true':
                queryset = queryset.filter(quantity__gt=0)
            elif in_stock.lower() == 'false':
                queryset = queryset.filter(quantity=0)

        # Price range filter
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'


class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductUpdateView(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'


class ProductDeleteView(generics.DestroyAPIView):
    queryset = Product.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class ProductSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        serializer = ProductSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        queryset = Product.objects.filter(is_active=True)

        # Search query
        q = data.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(category__title__icontains=q)
            )

        # Category filter
        category = data.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        # Price filters
        min_price = data.get('min_price')
        max_price = data.get('max_price')

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # In stock filter
        in_stock = data.get('in_stock')
        if in_stock is not None:
            if in_stock:
                queryset = queryset.filter(quantity__gt=0)
            else:
                queryset = queryset.filter(quantity=0)

        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data)