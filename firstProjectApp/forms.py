from django import forms
from .models import Recipe, RecipeStep, Ingredient, IngredientAmount
from django.core.exceptions import NON_FIELD_ERRORS


#
# Raise errors here when cleaning to pass back to frontend
#
class RecipeCreateForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['name', 'description', 'ingredients', 'duration', 'public']


class IngredientCreateForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'user']
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "You have already added this ingredient.",
            }
        }


class RecipeStepUpdateForm(forms.ModelForm):
    class Meta:
        model = RecipeStep
        fields = ["shortDesc", "description", "duration"]

    def clean_shortDesc(self):
        short_desc = self.cleaned_data['shortDesc']
        original_short_desc = self.data['shortDesc']
        if short_desc == None:
            return original_short_desc
        return short_desc

    def clean_description(self):
        description = self.cleaned_data['description']
        original_description = self.data['description']
        if description == None:
            return original_description
        return description




class IngredientAmountCreateForm(forms.ModelForm):
    class Meta:
        model = IngredientAmount
        fields = ['amount', 'user', 'units']
