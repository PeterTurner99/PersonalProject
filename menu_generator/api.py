import json
from datetime import timedelta
from typing import List

from dateutil.parser import parse
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from firstProjectApp.models import Recipe
from menu_generator.forms import MenuAndTimeForm, MenuAndTimeUpdateForm, RecurringTaskForm
from menu_generator.models import MenuAndTime, RepeatingTask
from menu_generator.schema import IngredientList, RecurringTaskSchema, SearchSchema, MenuListSchema, MealAddSchema, errorSchema, MealUpdateSchema, \
    MenuListAndDateSchema
from django.utils import timezone

from menu_generator.utils import date_range, tasks_from_date_range

router = Router()


#  Recipe search
#  random on empty search
#   if not search
#   list (recipes)
#   random.sample(recipe_list, 5)
#
#
@router.post('search/', response=List[MenuListSchema], auth=JWTAuth())
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


@router.post('recurring/', auth=JWTAuth())
def add_recurring_task(request, data: RecurringTaskSchema):
    data_dict = data.dict()
    data_dict['user'] = request.user
    form_data = RecurringTaskForm(data=data_dict)
    if form_data.is_valid():
        form_data.save()
        return JsonResponse(status=200, data={})
    return HttpResponse()

@router.post('search/month/', auth=JWTAuth())
def get_month_info(request, data: SearchSchema):
    data = data.dict()
    search_date = data.get('search')
    datetime_obj = parse(search_date)
    date_obj = datetime_obj.date()
    start_date = date_obj - timedelta(days=5)
    user = request.user
    date_task_dict = tasks_from_date_range(start_date,43, user)
    date_task_list_new = []
    for date_task_date, date_task_list in date_task_dict.items():
        date_task_list_new.append({'date':date_task_date,'recurringTasks':date_task_list})
    return date_task_list_new

@router.post('search/week/', auth=JWTAuth())
def get_week_info(request, data: SearchSchema):
    data = data.dict()
    search_date = data.get('search')
    datetime_obj = parse(search_date)
    date_obj = datetime_obj.date()
    start_date = date_obj 
    user = request.user
    date_task_dict = tasks_from_date_range(start_date,7, user)
    for date in date_range(start_date,7):
        if date.isoformat() not in date_task_dict.keys():
            date_task_dict[date.isoformat()] = []
    date_task_list_new = []
    for date_task_date, date_task_list in sorted(date_task_dict.items()):
        date_task_list_new.append({'date':date_task_date,'recurringTasks':date_task_list})
    return date_task_list_new



@router.post('month/', auth=JWTAuth(), response={200: List[MenuListAndDateSchema]})
def get_month_result(request, data: SearchSchema):
    data = data.dict()
    search_date = data.get('search')
    datetime_obj = parse(search_date)
    date_obj = datetime_obj.date()
    start_date = date_obj - timedelta(days=5)
    end_date = date_obj + timedelta(weeks=6)
    menus = MenuAndTime.objects.filter(
        date__gt=start_date, date__lte=end_date, type='d', user=request.user)
    return menus


@router.post('add/', response={200: List[MenuListSchema],
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


@router.post('required/', response={200: IngredientList}, auth=JWTAuth())
def get_required_ingredients(request, data: SearchSchema):
    data = data.dict()
    search_range = data.get('range', 7)
    ingredient_dict = {}
    date_obj = timezone.now().date()
    date_future = date_obj + timedelta(days=search_range)
    menus = MenuAndTime.objects.filter(
        date__gte=date_obj, date__lt=date_future, user=request.user)
    for menu in menus:
        ingredients = menu.recipe.ingredients.all()
        for ingredient_and_amount in ingredients:
            ingredient = ingredient_and_amount.ingredient
            amount = ingredient_and_amount.amount
            units = ingredient_and_amount.units
            if ingredient in ingredient_dict:
                if units.name in ingredient_dict[ingredient.name.capitalize()]:
                    ingredient_dict[ingredient.name.capitalize(
                    )][units.name.capitalize()] += amount
                else:
                    ingredient_dict[ingredient.name.capitalize(
                    )][units.name.capitalize()] = amount
            else:
                ingredient_dict[ingredient.name.capitalize()] = {
                    units.name.capitalize(): amount}
    return {'ingredients': json.dumps(ingredient_dict)}


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
