from django.contrib.auth import get_user_model
from django.db import models

from firstProjectApp.models import Recipe

User = get_user_model()


# Create your models here.


class MenuAndTime(models.Model):
    MEAL_TYPES = [
        ('d', 'Dinner'),
    ]
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    date = models.DateField()
    type = models.CharField(max_length=11, choices=MEAL_TYPES, default='d')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    @property
    def type_display(self):
        return self.get_type_display()

    @property
    def get_date_str(self):
        return self.date.isoformat()

    class Meta:
        unique_together = ('date', 'type', 'user')
