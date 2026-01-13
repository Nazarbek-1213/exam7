from django.urls import path
from . import views


urlpatterns = [


    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('verify-code/', views.VerifyCode.as_view(), name='verify-code'),
    path('new-verify-code/', views.NewVerifyCode.as_view(), name='new-verify-code'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('login/refresh/', views.LoginRefreshView.as_view(), name='login-refresh'),
    path('logout/', views.LogOutView.as_view(), name='logout'),

    # Password management
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),

    # User profile
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/update/', views.UserChangeView.as_view(), name='profile-update'),
    path('profile/photo/', views.UserPhotoUploadView.as_view(), name='profile-photo'),

]


