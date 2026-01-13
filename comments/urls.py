from django.urls import path
from .views import (ProductCommentsListView, CommentCreateView,
                    CommentUpdateView, CommentDeleteView,
                    AllCommentsListView)

urlpatterns = [
    # Product comments
    path('products/<slug:slug>/comments/',
         ProductCommentsListView.as_view(), name='product-comments'),
    path('products/<slug:slug>/comments/create/',
         CommentCreateView.as_view(), name='comment-create'),

    # Comment CRUD
    path('comments/<int:id>/update/',
         CommentUpdateView.as_view(), name='comment-update'),
    path('comments/<int:id>/delete/',
         CommentDeleteView.as_view(), name='comment-delete'),

    # All comments
    path('comments/', AllCommentsListView.as_view(), name='all-comments'),
]