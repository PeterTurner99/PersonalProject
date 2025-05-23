import datetime
from django import forms
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from firstProjectApp.models import Recipe
from menu_generator.utils import week_of_month

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


class RepeatingTask(models.Model):
    FREQUENCY_TYPES = [
        ('m', 'Monthly'),
        ('d', 'Daily'),
        ('w', 'Weekly'),
        ('f', 'Fortnightly')
    ]
    DAYS_OF_WEEK = [
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
        (None,'None'),
    ]
    frequency = models.CharField(
        max_length=5, choices=FREQUENCY_TYPES, default='w')
    time = models.TimeField()
    day = models.CharField(
        max_length=5, choices=DAYS_OF_WEEK, null=True, blank=True)
    created_date = models.DateField(auto_now_add=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)])
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    active = models.BooleanField(default=True)
    
    @property
    def get_hour_int(self):
        hour = self.time.hour
        return hour
    
    def matching_date(self,date_given):
        frequency = self.frequency
        if frequency == 'd':
            return True
        day = self.day
        int_day = int(day)
        created_date = self.created_date
        
        created_weekday = created_date.weekday()
        days_extra = int_day - created_weekday
        if days_extra < 0:
            days_extra = days_extra + 7 
        given_weekday = date_given.weekday()
        days_since_created = abs((date_given - created_date).days) + days_extra
        if int_day != given_weekday:
            return False
        if frequency == 'm':
            required_week_of_month = min(week_of_month(created_date),4)
            given_week_of_month = min(week_of_month(date_given), 4)
            return (required_week_of_month == given_week_of_month)
        if frequency == 'w':
            return True
        if frequency == 'f':
            if days_since_created % 14 != 0:
                return False
            return True