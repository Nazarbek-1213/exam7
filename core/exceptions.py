from rest_framework.exceptions import APIException

class CartEmptyException(APIException):
    status_code = 400
    default_detail = 'Savat bo\'sh'
    default_code = 'cart_empty'

class OrderNotFoundException(APIException):
    status_code = 404
    default_detail = 'Buyurtma topilmadi'
    default_code = 'order_not_found'