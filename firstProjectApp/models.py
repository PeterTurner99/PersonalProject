from django.db import models
from django.contrib.auth import get_user_model
# Create your models here.
User = get_user_model()



class Unit(models.Models):
    name = models.CharField(max_length=30)
    conversionToGrams = models.FloatField()
    

class Ingredient(models.Model):
    amount = models.FloatField()
    units = models.ForeignKey(Unit, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    public = models.BooleanField(default=False)
    
    def convertUnit(self, newUnit):
        currentUnit = self.units
        currentAmount = self.amount
        return currentAmount * (currentUnit.conversionToGrams / newUnit.conversionToGrams)

    
    
class Recipe(models.Model):
    ingredients = models.ManyToManyField(Ingredient)
    description = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    public = models.BooleanField(default=False)
    
    
class Tags(models.Model):
    tag = models.CharField(max_length=30)
    tagDescription = models.TextField(null=True, blank=True)
    recipeTag = models.ManyToManyField(Recipe)
    ingredientTag = models.ManyToManyField(Ingredient)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    public = models.BooleanField(default=False)