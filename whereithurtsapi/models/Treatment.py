""" Database module for Treatments """
from django.db import models
from django.db.models.deletion import DO_NOTHING


class Treatment(models.Model):
    # Bodypart and Treatment Type are developer-defined so should not be deleted, but ideally will be handled better if accidentally deleted (e.g. fallback category)
    added_by = models.ForeignKey("Patient", on_delete=DO_NOTHING)
    bodypart = models.ForeignKey("Bodypart", on_delete=DO_NOTHING)
    treatmenttype = models.ForeignKey("TreatmentType", on_delete=DO_NOTHING)
    name = models.CharField(max_length=75)
    added_on = models.DateTimeField()
    notes = models.CharField(max_length=400)
    public = models.BooleanField(default=False)

    @property
    def healing_count(self):
        return self.healing_treatments.all().count()

    @property
    def links(self):
        return self.treatmentlink_set.all()

    @property
    def hurts(self):
        hurt_treatments = self.hurt_treatments.all()
        return [ht.hurt for ht in hurt_treatments]

    @property
    def date_added(self):
        return self.added_on.strftime('%-m/%d/%Y')

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, new_value):
        self._owner = new_value


