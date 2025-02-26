from django.contrib import admin
from .models import Recipe, RecipeStep, Ingredient, Unit

# Register your models here.

admin.site.register(Recipe)
admin.site.register(RecipeStep)
admin.site.register(Unit)
