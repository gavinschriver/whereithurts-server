""" Database module for Updates """
from django.db import models

class Update(models.Model):
    
    hurt = models.ForeignKey("Hurt", on_delete=models.CASCADE)
    added_on = models.DateTimeField()
    pain_level = models.IntegerField()
    notes = models.CharField(max_length=300)

    """ property to establish if this Update is the first one for a Hurt, 
        which dictates whether or not it is editable as a standalone Update
    """
    @property
    def is_first_update(self):
        if self.hurt.first_update_id == self.id:
            return True
        return False

    @property
    def date_added(self):
        return self.added_on.strftime('%-m/%d/%Y')

    @property
    def pain_level_difference(self):
        try:
            previous = self.get_previous_by_added_on(hurt=self.hurt)
            if previous.pain_level > self.pain_level:
                return f"Down {previous.pain_level - self.pain_level} from last update"
            elif previous.pain_level < self.pain_level:
                return f"Up {self.pain_level - previous.pain_level} from last update"
            else:
                return "No change from last update"
        except:
            pass

