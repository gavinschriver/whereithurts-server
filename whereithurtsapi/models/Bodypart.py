"""Database Bodypart module"""
from django.db import models


class Bodypart(models.Model):
    """Database Bodypart model

    Defined internally"""
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='icons/bodyparts', height_field=None, width_field=None, null=True, max_length=None)
