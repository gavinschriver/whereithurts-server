""" Database module for HurtHealings """
from django.db import models

class HurtHealing(models.Model):
    hurt = models.ForeignKey("Hurt", related_name="hurt_healings", on_delete=models.CASCADE)
    healing = models.ForeignKey("Healing", related_name="hurt_healings", on_delete=models.CASCADE)