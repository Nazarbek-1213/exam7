from django.db import models
import uuid

class BaseModel(models.Model):
    id = models.UUIDField(unique=True, editable=False, primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True