from django.contrib import admin

from .models import MenuAndTime, RepeatingTask

# Register your models here.

admin.site.register(MenuAndTime)
admin.site.register(RepeatingTask)