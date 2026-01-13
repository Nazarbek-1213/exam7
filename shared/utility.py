import re
from rest_framework.exceptions import ValidationError
from django.core.mail import send_mail
from rest_framework.response import Response

import config.settings

email_regex = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
phone_regex = re.compile(r"^(?:\+998[ -]?)?(?:[1-9]\d{1,2}|[5789]\d)\s?\d{3}\s?\d{2}\s?\d{2}$")
username_regex = re.compile(r"^[A-Za-z][A-Za-z0-9_]{7,29}$")

def email_or_phone(email_phone_number):
    if re.fullmatch(email_regex, email_phone_number):
        data = 'email'
    elif re.fullmatch(phone_regex, email_phone_number):
        data = 'phone'
    else:
        data = {
            'succes': 'False',
            'message':'Telefon raqam yoki email xato kiritildi'
        }
        raise ValidationError(data)

    return data


def user_check_type(userinput):
    if re.fullmatch(email_regex, userinput):
        data = 'email'
    elif re.fullmatch(phone_regex, userinput):
        data = 'phone'
    elif re.fullmatch(username_regex, userinput):
        data = 'username'
    else:
        data = {
            'succes': 'False',
            'message':'Telefon raqam yoki email yoki username-ni xato kiritildi'
        }
        raise ValidationError(data)

    return data





def send_email(to_email, code):
    """
    Gmail orqali tasdiqlash kodini yuboradi
    """
    subject = "Sizning tasdiqlash kodingiz"
    message = f"Salom!\nSizning tasdiqlash kodingiz: {code}\nKod 5 daqiqa ichida amal qiladi."
    email_form = None  # settings.DEFAULT_FROM_EMAIL ishlaydi
    recipient_list = [to_email]

    try:
        send_mail(subject, message, email_form, recipient_list)
    except Exception as e:
        print("Email yuborishda xato:", e)