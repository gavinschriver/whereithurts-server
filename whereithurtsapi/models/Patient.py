from django.db import models
from django.contrib.auth.models import User


class Patient(models.Model):
    """ Model for Patients resource """
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def email(self):
        return self.user.email

    @property
    def username(self):
        return self.user.username

    @property
    def hurts(self):
        return self.hurt_set.all()

    @property
    def healings(self):
        return self.healing_set.all()

    """ property to return all updates added by this user """
    @property
    def updates(self):
        hurts = self.hurt_set.all()
        #intialize empty lists for the udpate querysets for each hurt, and for the eventual
        # final list of update instances
        update_qsets = []
        updates = []
        ## add the update_sqset for each hurt to the update_qsets list
        for hurt in hurts:
            update_qsets.append(hurt.update_set.exclude(id=hurt.first_update_id))
        ## for each update_qset, append each update entry in it to the final list
        for update_qset in update_qsets:
            for update in update_qset:
                updates.append(update)
        return updates





