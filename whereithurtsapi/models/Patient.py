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