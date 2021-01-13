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

    @property
    def healings(self):
        hurt_healings= self.hurt_healings.all()
        return [hh.healing for hh in hurt_healings]

    @property 
    def latest_pain_level(self):
        last_update = self.update_set.all().order_by('-added_on')[0]
        return last_update.pain_level
    
    @property
    def updates(self):
        return self.update_set.all().order_by('added_on')

    @property
    def last_update(self):
        last_update = self.update_set.all().order_by('-added_on')[0]
        return last_update.added_on
    
    @property
    def first_update_id(self):
        return self.update_set.all().order_by('added_on')[0].id

    #this doesn't work, its based on a UTC timestamp
    @property
    def date_added(self):
        return self.added_on.strftime('%-m/%d/%Y')

    @property
    def owner(self):
        return self._owner
    
    @owner.setter
    def owner(self, new_value):
        self._owner = new_value
    

