import random
import uuid
from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator

from shared.models import BaseModel
from rest_framework_simplejwt.tokens import RefreshToken

ORDINARY_USER, MANAGER, ADMIN = ('ordinary_user', 'manager', 'admin')
NEW, CODE_VERIFIED, DONE, CLIENT = ('new', 'code_verified', 'done', 'client')
VIA_EMAIL, VIA_PHONE = ('via_email', 'via_phone')


class User(AbstractUser, BaseModel):
    USER_ROLE = (
        (ORDINARY_USER, ORDINARY_USER),
        (MANAGER, MANAGER),
        (ADMIN, ADMIN)
    )
    AUTH_STATUS = (
        (NEW, NEW),
        (CODE_VERIFIED, CODE_VERIFIED),
        (DONE, DONE),
        (CLIENT, CLIENT),
    )
    AUTH_TYPE = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE)
    )
    user_role = models.CharField(max_length=29, choices=USER_ROLE, default=ORDINARY_USER)
    auth_status = models.CharField(max_length=29, choices=AUTH_STATUS, default=NEW)
    auth_type = models.CharField(max_length=29, choices=AUTH_TYPE, null=True, blank=True)
    phone_number = models.CharField(max_length=13, null=True, blank=True, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    photo = models.ImageField(upload_to='users_photo/', null=True,
                              blank=True,
                              validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])])

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def generate_code(self, verify_type):
        code = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        UserConfirmation.objects.create(
            user_id=self.id,
            code=code,
            verify_type=verify_type
        )
        return code

    def check_username(self):
        if not self.username:
            temp_username = f"username{str(uuid.uuid4()).split('-')[-1]}"
            while User.objects.filter(username=temp_username).exists():
                temp_username = f"{temp_username}{random.randint(0, 9)}"
            self.username = temp_username

    def check_pass(self):
        if not self.password:
            temp_pass = f"password{str(uuid.uuid4()).split('-')[-1]}"
            self.password = temp_pass

    def hashing_pass(self):
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.set_password(self.password)

    def check_email(self):
        if self.email:
            normalize_email = self.email.lower()
            self.email = normalize_email

    def token(self):
        refresh = RefreshToken.for_user(self)
        data = {
            'access': str(refresh.access_token),
            'refresh_token': str(refresh)
        }
        return data

    def clean(self):
        self.check_username()
        self.check_email()
        self.check_pass()
        self.hashing_pass()

    def save(self, *args, **kwargs):
        self.clean()
        return super(User, self).save(*args, **kwargs)


EXPIRATION_EMAIL = 3
EXPIRATION_PHONE = 2


class UserConfirmation(BaseModel):
    VERIFY_TYPE = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE)
    )
    code = models.CharField(max_length=4)
    verify_type = models.CharField(max_length=29, choices=VERIFY_TYPE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='verify_codes')
    expiration_time = models.DateTimeField(null=True, blank=True)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user.__str__())

    def save(self, *args, **kwargs):
        if not self.expiration_time:
            if self.verify_type == VIA_EMAIL:
                self.expiration_time = datetime.now() + timedelta(minutes=EXPIRATION_EMAIL)
            else:
                self.expiration_time = datetime.now() + timedelta(minutes=EXPIRATION_PHONE)
        super(UserConfirmation, self).save(*args, **kwargs)