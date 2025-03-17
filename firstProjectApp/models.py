from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# Create your models here.
User = get_user_model()


class Unit(models.Model):
    name = models.CharField(max_length=30)
    conversionToGrams = models.FloatField(null=True)

class Ingredient(models.Model):
    name = models.CharField(max_length=250)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    public = models.BooleanField(default=True)
    calories = models.IntegerField('Calories per 100g', null=True, blank=True)

    class Meta:
        unique_together = ('name', 'user')
    # nutritional info
    # nutrients per calorie


class IngredientAmount(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, null=True)
    amount = models.FloatField()
    units = models.ForeignKey(Unit, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    details = models.TextField(null=True, blank=True)
    public = models.BooleanField(default=False)

    def convert_unit(self, new_unit):
        current_unit = self.units
        current_amount = self.amount
        return current_amount * (current_unit.conversionToGrams / new_unit.conversionToGrams)

    @property
    def name(self):
        return self.ingredient.name

    @property
    def units_str(self):
        return self.units.name

    class Meta:
        unique_together = ('ingredient', 'amount', 'units', 'details')

class Recipe(models.Model):
    name = models.CharField(max_length=250, null=True, unique=True)
    ingredients = models.ManyToManyField(IngredientAmount, blank=True)
    description = models.TextField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    public = models.BooleanField(default=False)
    source = models.URLField(null=True, blank=True)
    serves = models.IntegerField(default=1)


class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    shortDesc = models.CharField(max_length=250, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    order = models.IntegerField(validators=[MinValueValidator(1)], null=True, blank=True)

    class Meta:
        ordering = ['order']
        unique_together = ('recipe', 'order')


class Tags(models.Model):
    tag = models.CharField(max_length=30)
    tagDescription = models.TextField(null=True, blank=True)
    recipeTag = models.ManyToManyField(Recipe)
    ingredientTag = models.ManyToManyField(IngredientAmount)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    public = models.BooleanField(default=False)


class RecipeReview(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MaxValueValidator(5), MinValueValidator(1)], null=True)
    reviewText = models.TextField(null=True, blank=True)
    publicRating = models.BooleanField(default=True)
    publicReview = models.BooleanField(default=True)
