from django.urls import path
from .views import (ProductListView, ProductDetailView,
                    ProductCreateView, ProductUpdateView,
                    ProductDeleteView, ProductSearchView)

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('search/', ProductSearchView.as_view(), name='product-search'),
    path('<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('create/', ProductCreateView.as_view(), name='product-create'),
    path('<slug:slug>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('<slug:slug>/delete/', ProductDeleteView.as_view(), name='product-delete'),
]