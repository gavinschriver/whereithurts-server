""" Database module for HurtHealings """
from django.db import models

class HurtHealing(models.Model):
    hurt = models.ForeignKey("Hurt", related_name="HurtHealing", on_delete=models.CASCADE)
    healing = models.ForeignKey("Healing", related_name="HurtHealing", on_delete=models.CASCADE)