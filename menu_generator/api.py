import json
from datetime import timedelta
from typing import List

from dateutil.parser import parse
from django.http import Http404
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from firstProjectApp.models import Recipe
from menu_generator.forms import MenuAndTimeForm, MenuAndTimeUpdateForm
from menu_generator.models import MenuAndTime
from menu_generator.schema import SearchSchema, MenuListSchema, MealAddSchema, errorSchema, MealUpdateSchema, \
    MenuListAndDateSchema

router = Router()


#  Recipe search
#  random on empty search
#   if not search
#   list (recipes)
#   random.sample(recipe_list, 5)
#
#
@router.post('/search/', response=List[MenuListSchema], auth=JWTAuth())
def calendar_search(request, data: SearchSchema):
    data = data.dict()
    search_date = data.get('search')
    datetime_obj = parse(search_date)
    date_obj = datetime_obj.date()
    menus = MenuAndTime.objects.filter(date=date_obj, user=request.user)
    if not menus:
        raise Http404(
            "No menus found"
        )
    return menus


@router.post('/month/', auth=JWTAuth(), response={200: List[MenuListAndDateSchema]})
def get_month_result(request, data: SearchSchema):
    data = data.dict()
    search_date = data.get('search')
    datetime_obj = parse(search_date)
    date_obj = datetime_obj.date()
    start_date = date_obj - timedelta(days=5)
    end_date = date_obj + timedelta(weeks=6)
    menus = MenuAndTime.objects.filter(date__gt=start_date, date__lte=end_date, type='d', user=request.user)
    return menus


@router.post('/add/', response={200: List[MenuListSchema],
                                400: errorSchema}, auth=JWTAuth())
def add_meal(request, data: MealAddSchema):
    data = data.dict()
    form_data_dict = {}
    recipe = Recipe.objects.filter(name=data.get('recipe'))
    if not recipe.exists:
        raise Http404('Invalid recipe')
    search_date = data.get('date')
    datetime_obj = parse(search_date)
    date_obj = datetime_obj.date()
    form_data_dict['date'] = date_obj
    form_data_dict['recipe'] = recipe.first()
    form_data_dict['type'] = data.get('time')
    form_data_dict['user'] = request.user
    new_menu_and_time_form = MenuAndTimeForm(
        form_data_dict
    )
    if new_menu_and_time_form.is_valid():
        new_menu_and_time_form.save()
        menus = MenuAndTime.objects.filter(date=date_obj)
        return menus
    else:
        form_errors = json.loads(
            new_menu_and_time_form.errors.as_json())
        errors_list = []
        for error_list in form_errors.values():
            error = error_list[0]
            errors_list.append(error.get('message', error.get('name')))
        error_dict = {'messages': errors_list}
        return 400, error_dict


@router.put('update/{entry_id}/', response={200: MenuListSchema,
                                            400: errorSchema}, auth=JWTAuth())
def update_meal(request, entry_id: int, data: MealUpdateSchema):
    obj = get_object_or_404(MenuAndTime, pk=entry_id)
    data_dict = data.dict()
    form = MenuAndTimeUpdateForm(data_dict, instance=obj)
    if form.is_valid():
        cleaned_data = form.cleaned_data
        for attr, value in cleaned_data.items():
            if value != None:
                setattr(obj, attr, value)
        obj.save()
        return 200, obj
    else:
        form_errors = json.loads(
            form.errors.as_json())
        errors_list = []
        for error_list in form_errors.values():
            error = error_list[0]
            errors_list.append(error.get('message', error.get('name')))
        error_dict = {'messages': errors_list}
        return 400, error_dict
