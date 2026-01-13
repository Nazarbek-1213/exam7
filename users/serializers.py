from datetime import datetime

from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.tokens import AccessToken

from .models import User, VIA_EMAIL, VIA_PHONE, CODE_VERIFIED, DONE, CLIENT, NEW, UserConfirmation
from shared.utility import email_or_phone, user_check_type, send_email
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from django.contrib.auth import authenticate


class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    auth_type = serializers.CharField(read_only=True, required=False)
    auth_status = serializers.CharField(read_only=True, required=False)

    def __init__(self, *args, **kwargs):
        super(SignUpSerializer, self).__init__(*args, **kwargs)
        self.fields['email_phone_number'] = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id',
            'auth_type',
            'auth_status'
        ]
        extra_kwargs = {
            'auth_type': {'read_only': True},
            'auth_status': {'read_only': True}
        }

    def create(self, validated_data):
        # Remove the extra field that's not in the model
        validated_data.pop('email_phone_number', None)

        user = super(SignUpSerializer, self).create(validated_data)
        if user.auth_type == VIA_EMAIL:
            code = user.generate_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.generate_code(VIA_PHONE)
            print(f"Telefon raqamiga yuborilgan kod: {code}")
        else:
            raise ValidationError({
                'success': False,
                'message': 'Telefon raqam yoki emailni togri kiriting'
            })
        user.auth_status = CODE_VERIFIED
        user.save()
        return user

    def validate(self, data):
        data = self.auth_validate(data)
        return data

    @staticmethod
    def auth_validate(data):
        user_input = str(data.get('email_phone_number')).lower().strip()
        user_input_type = email_or_phone(user_input)

        if user_input_type == 'email':
            data = {
                'email': user_input,
                'auth_type': VIA_EMAIL
            }
        elif user_input_type == 'phone':
            data = {
                'phone_number': user_input,
                'auth_type': VIA_PHONE
            }
        else:
            raise ValidationError({
                'success': False,
                'message': 'Telefon raqam yoki emailni kiriting'
            })

        return data

    def validate_email_phone_number(self, value):
        value = value.lower().strip()
        if value and User.objects.filter(email=value).exists():
            raise ValidationError('Bu email allaqachon mavjud')
        elif value and User.objects.filter(phone_number=value).exists():
            raise ValidationError('Bu telefon raqam allaqachon mavjud')
        return value

    def to_representation(self, instance):
        data = super(SignUpSerializer, self).to_representation(instance)
        data.update(instance.token())
        return data


class VerifyCodeSerializer(serializers.Serializer):
    code = serializers.CharField(
        max_length=4,
        required=True,
        help_text="Ro'yxatdan o'tishda yuborilgan 4 xonali tasdiqlash kodi"
    )

    def validate_code(self, value):
        if not value.strip():
            raise ValidationError("Kod bo'sh bo'lishi mumkin emas")
        if len(value) != 4 or not value.isdigit():
            raise ValidationError("Kod 4 xonali raqam bo'lishi kerak")
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        code = attrs.get('code')

        # UserConfirmation orqali tekshirish
        verify = UserConfirmation.objects.filter(
            user=user,
            code=code,
            confirmed=False,
            expiration_time__gte=datetime.now()
        )

        if not verify.exists():
            raise ValidationError({
                'success': False,
                'message': 'Kod eskirgan yoki xato'
            })

        # Kodni tasdiqlash
        verify.update(confirmed=True)

        # Foydalanuvchi auth_status yangilanishi
        if user.auth_status == CODE_VERIFIED:
            user.auth_status = DONE
            user.save()

        return attrs


class UserChangeInfoSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'password',
            'confirm_password'
        )
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'confirm_password': {'write_only': True, 'required': False}
        }

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)

        if password and not confirm_password:
            raise ValidationError({
                'success': False,
                'message': 'Tasdiqlash parolini kiriting'
            })

        if confirm_password and not password:
            raise ValidationError({
                'success': False,
                'message': 'Yangi parolni kiriting'
            })

        if password and confirm_password and password != confirm_password:
            raise ValidationError({
                'success': False,
                'message': 'Parollar mos emas'
            })

        if password:
            validate_password(password)

        return data

    def validate_username(self, username):
        if self.instance and self.instance.username == username:
            return username

        user = User.objects.filter(username=username).exists()
        if user:
            raise ValidationError({
                'success': False,
                'message': 'Username mavjud'
            })
        if username.isdigit() or len(username) < 5:
            raise ValidationError({
                'success': False,
                'message': 'Username talabga mos kelmaydi'
            })
        return username

    def validate_first_name(self, first_name):
        if len(first_name.strip()) < 2:
            raise ValidationError({
                'success': False,
                'message': 'Ism juda qisqa'
            })
        return first_name.strip()

    def validate_last_name(self, last_name):
        if len(last_name.strip()) < 2:
            raise ValidationError({
                'success': False,
                'message': 'Familiya juda qisqa'
            })
        return last_name.strip()

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.first_name = validated_data.get('first_name', instance.first_name)

        password = validated_data.get('password')
        if password:
            instance.set_password(password)

        if instance.auth_status == DONE:
            instance.auth_status = CLIENT

        instance.save()
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'username',
            'message',
            'auth_status',
            'auth_type',
        )

    def get_username(self, obj):
        # Agar CLIENT bo'lsa username ko'rsatilsin, aks holda None
        if obj.auth_status == CLIENT:
            return obj.username
        return None

    def get_message(self, obj):
        if obj.auth_status == CLIENT:
            return "Foydalanuvchi to'liq ro'yxatdan o'tgan"
        elif obj.auth_status == DONE:
            return "Foydalanuvchi hali CLIENT emas, lekin to'liq ro'yxatdan o'tgan"
        return "Foydalanuvchi hali to'liq ro'yxatdan o'tmagan"


class UserPhotoSerializer(serializers.Serializer):
    photo = serializers.ImageField()

    def update(self, instance, validated_data):
        photo = validated_data.get('photo')
        if str(photo).endswith('.webp'):
            raise ValidationError({
                'success': False,
                'message': 'Rasm formati mos kelmaydi'
            })

        if photo:
            instance.photo = photo
            instance.save()

        return instance


class LoginSerializer(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super(LoginSerializer, self).__init__(*args, **kwargs)
        self.fields['userinput'] = serializers.CharField(required=True)
        self.fields['username'] = serializers.CharField(required=False, read_only=True)

    def auth_validate(self, data):
        user_input = data.get('userinput').lower().strip()
        user_input_type = user_check_type(user_input)

        if user_input_type == 'username':
            username = user_input
        elif user_input_type == "email":
            user = self.get_user(email__iexact=user_input)
            username = user.username
        elif user_input_type == 'phone':
            user = self.get_user(phone_number=user_input)
            username = user.username
        else:
            raise ValidationError({
                'success': False,
                'message': "Siz email, username yoki telefon raqami jonatishingiz kerak"
            })

        authentication_kwargs = {
            self.username_field: username,
            'password': data['password']
        }
        current_user = User.objects.filter(username__iexact=username).first()

        if current_user is not None and current_user.auth_status in [NEW, CODE_VERIFIED]:
            raise ValidationError({
                'success': False,
                'message': "Siz royhatdan toliq otmagansiz!"
            })

        user = authenticate(**authentication_kwargs)
        if user is not None:
            self.user = user
        else:
            raise ValidationError({
                'success': False,
                'message': "Siz kiritgan login yoki parol xato. Tekshiring va qaytadan kiriting"
            })

    def validate(self, data):
        self.auth_validate(data)
        if self.user.auth_status not in [DONE, CLIENT]:
            raise PermissionDenied("Siz login qila olmaysiz. Ruxsatingiz yoq")

        data = self.user.token()
        data['auth_status'] = self.user.auth_status
        data['full_name'] = self.user.full_name
        data['user_id'] = str(self.user.id)
        return data

    def get_user(self, **kwargs):
        users = User.objects.filter(**kwargs)
        if not users.exists():
            raise ValidationError({
                "message": "No active account found"
            })
        return users.first()


class LoginRefreshSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        access_token_instance = AccessToken(data['access'])
        user_id = access_token_instance['user_id']
        user = get_object_or_404(User, id=user_id)
        update_last_login(None, user)
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email_or_phone = attrs.get('email_or_phone', None)
        if email_or_phone is None:
            raise ValidationError({
                "success": False,
                'message': "Email yoki telefon raqami kiritilishi shart!"
            })

        user = User.objects.filter(Q(phone_number=email_or_phone) | Q(email=email_or_phone))
        if not user.exists():
            raise NotFound(detail="User not found")

        attrs['user'] = user.first()
        return attrs


class ResetPasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8, required=True, write_only=True)
    confirm_password = serializers.CharField(min_length=8, required=True, write_only=True)

    class Meta:
        model = User
        fields = (
            'password',
            'confirm_password'
        )

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)

        if password != confirm_password:
            raise ValidationError({
                'success': False,
                'message': "Parollaringiz qiymati bir-biriga teng emas"
            })

        if password:
            validate_password(password)

        return data

    def update(self, instance, validated_data):
        password = validated_data.pop('password')
        instance.set_password(password)
        instance.save()
        return instance