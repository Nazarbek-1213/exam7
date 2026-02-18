from django.urls import path
from .views import *

urlpatterns = [
    path('', CartDetailView.as_view(), name='cart-detail'),
    path('add/', AddToCartView.as_view(), name='cart-add'),
    path('remove/', RemoveFromCartView.as_view(), name='cart-remove'),
    path('clear/', ClearCartView.as_view(), name='cart-clear'),
    path('update/', UpdateCartItemView.as_view(), name='cart-update'),
]