from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from drf_yasg.utils import swagger_auto_schema
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import status

from shared.utility import send_email, email_or_phone
from users.models import User, VIA_EMAIL, VIA_PHONE, DONE, CLIENT, CODE_VERIFIED
from users.serializers import SignUpSerializer, UserChangeInfoSerializer, UserPhotoSerializer, ResetPasswordSerializer, \
    LoginSerializer, LoginRefreshSerializer, LogoutSerializer, ForgotPasswordSerializer, UserProfileSerializer, \
    VerifyCodeSerializer


class SignUpView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = (AllowAny,)


class VerifyCode(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(request_body=VerifyCodeSerializer, responses={200: 'OK'})
    def post(self, request, *args, **kwargs):
        serializer = VerifyCodeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = {
            'success': True,
            'auth_status': user.auth_status,
            'access_token': user.token()['access'],
            'refresh': user.token()['refresh_token']
        }
        return Response(data)


class NewVerifyCode(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        self.check_code(user)

        if user.auth_type == VIA_EMAIL:
            code = user.generate_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.generate_code(VIA_PHONE)
            print(f"Telefon raqamiga yuborilgan kod: {code}")
        else:
            raise ValidationError({
                'success': 'False',
                'message': 'Telefon raqam yoki emailni togri kiriting'
            })

        data = {
            'success': True,
            'message': 'Kod yuborildi'
        }
        return Response(data)

    @staticmethod
    def check_code(user):
        verify = user.verify_codes.filter(confirmed=False, expiration_time__gte=datetime.now())
        if verify.exists():
            raise ValidationError({
                'success': False,
                'message': 'Sizda active code mavjud'
            })
        if user.auth_status in [CODE_VERIFIED, DONE, CLIENT]:
            raise ValidationError({
                'success': False,
                'message': 'Sizda code tasdiqlangan'
            })
        return True


class UserChangeView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserChangeInfoSerializer
    http_method_names = ['patch', 'put']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        data = {
            'success': True,
            "message": "Sizning malumotlaringiz saqlandi",
            'auth_status': self.request.user.auth_status,
        }
        return Response(data, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class UserPhotoUploadView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserPhotoSerializer
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['patch']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        data = {
            'status': status.HTTP_200_OK,
            'message': 'Rasm o\'zgartirildi'
        }
        return Response(data)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class LoginRefreshView(TokenRefreshView):
    serializer_class = LoginRefreshSerializer


class LogOutView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = serializer.validated_data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            data = {
                'success': True,
                'message': "Siz tizimdan chiqdingiz"
            }
            return Response(data, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({
                'success': False,
                'message': 'Token xato'
            }, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email_or_phone_input = serializer.validated_data.get('email_or_phone')
        user = serializer.validated_data.get('user')

        # Determine if it's email or phone
        input_type = email_or_phone(email_or_phone_input)

        if input_type == 'phone':
            code = user.generate_code(VIA_PHONE)
            print(f"Telefon raqamiga yuborilgan kod: {code}")
        elif input_type == 'email':
            code = user.generate_code(VIA_EMAIL)
            send_email(email_or_phone_input, code)
        else:
            raise ValidationError({
                "success": False,
                'message': "Email yoki telefon raqami kiritilishi kerak"
            })

        return Response({
            "success": True,
            'message': "Tasdiqlash kodi muvaffaqiyatli yuborildi",
            "access": user.token()['access'],
            "refresh": user.token()['refresh_token'],
            "user_status": user.auth_status,
        }, status=status.HTTP_200_OK)


class ResetPasswordView(UpdateAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['put', 'patch']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        response = super(ResetPasswordView, self).update(request, *args, **kwargs)

        try:
            user = User.objects.get(id=response.data.get('id', self.request.user.id))
        except ObjectDoesNotExist:
            raise NotFound(detail='Foydalanuvchi topilmadi')

        return Response({
            'success': True,
            'message': "Parolingiz muvaffaqiyatli o'zgartirildi",
            'access': user.token()['access'],
            'refresh': user.token()['refresh_token'],
        }, status=status.HTTP_200_OK)