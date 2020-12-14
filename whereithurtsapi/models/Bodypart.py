"""Database Bodypart module"""
from django.db import models

class Bodypart(models.Model):
    """Database Bodypart model
    
    Defined internally"""
    name = models.CharField(max_length=50)
