from django.contrib import admin
from .models import PushNotification, Recipe, RecipeStep, Ingredient, Unit, IngredientAmount

# Register your models here.

admin.site.register(Recipe)
admin.site.register(RecipeStep)
admin.site.register(Unit)
admin.site.register(IngredientAmount)
admin.site.register(Ingredient)
admin.site.register(PushNotification)