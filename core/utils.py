from django.utils.text import slugify


def generate_slug(title, model_class):
    """
    Model uchun unique slug yaratish
    """
    slug = slugify(title)
    original_slug = slug
    counter = 1

    while model_class.objects.filter(slug=slug).exists():
        slug = f"{original_slug}-{counter}"
        counter += 1

    return slug


def calculate_cart_total(cart_items):
    """
    Savat umumiy narxini hisoblash
    """
    return sum(item.total_price for item in cart_items)