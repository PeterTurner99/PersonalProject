from dateutil.parser import parse
from django import forms
from django.core.exceptions import NON_FIELD_ERRORS

from firstProjectApp.models import Recipe
from .models import MenuAndTime


#
# Raise errors here when cleaning to pass back to frontend
#


class MenuAndTimeForm(forms.ModelForm):
    class Meta:
        model = MenuAndTime
        fields = ['recipe', 'date', 'type']
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "",
            }
        }


class MenuAndTimeUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(MenuAndTimeUpdateForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['recipe'] = forms.CharField(max_length=100)
        self.fields['date'] = forms.CharField(max_length=100)
        self.fields['recipe'].required = False
        self.fields['date'].required = False
        self.fields['type'].required = False

    class Meta:
        model = MenuAndTime
        fields = ['recipe', 'date', 'type']
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "",
            }
        }

    def clean_recipe(self):
        recipe = self.cleaned_data['recipe']
        recipe_obj = Recipe.objects.filter(name=recipe)
        if recipe_obj.exists():
            return recipe_obj.first()
        original_recipe = self.data['recipe']
        return original_recipe

    def clean_date(self):
        date = self.cleaned_data['date']
        original_date = self.instance.date
        if date == None or date == '':
            return original_date
        datetime_obj = parse(date)
        date_obj = datetime_obj.date()
        return date_obj

    def clean_type(self):
        type = self.cleaned_data['type']
        original_type = self.instance.type
        if type == None:
            return original_type
        return type
