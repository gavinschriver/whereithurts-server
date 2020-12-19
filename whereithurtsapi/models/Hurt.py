""" Database Hurt module """
from django.db import models

class Hurt(models.Model):
    """Database Hurt model"""

    patient = models.ForeignKey("Patient", on_delete=models.CASCADE)
    bodypart = models.ForeignKey("Bodypart", on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100)
    added_on = models.DateTimeField()
    is_active = models.BooleanField()

    @property
    def notes(self):
        first_update = self.update_set.order_by('added_on')[0]
        return f"{first_update.notes}"

    @property
    def pain_level(self):
        first_update = self.update_set.order_by('added_on')[0]
        return first_update.pain_level

    @property
    def healing_count(self):
        return self.hurt_healings.all().count()

    @property
    def treatments(self):
        hurt_treatments = self.hurt_treatments.all()
        return [ht.treatment for ht in hurt_treatments]
