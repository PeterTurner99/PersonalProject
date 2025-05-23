import json
import os
from random import sample
from typing import List
import re
from django.db.models import Max
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
import http_ece
from httplib2 import Http
from ingredient_parser import parse_ingredient
from isodate import parse_duration
from ninja import Router
from ninja_jwt.authentication import JWTAuth
import push_notifications
from recipe_scrapers import scrape_me, scrape_html
import requests
from .forms import RecipeCreateForm, RecipeStepUpdateForm, IngredientCreateForm, IngredientAmountCreateForm
from .models import PushNotification, Recipe, RecipeStep, Ingredient, Unit, IngredientAmount
from .schemas import IdSchema, PushNameSchema, PushNotificationInformation, RecipeEntryListSchema, RecipeEntryDetailSchema, RecipeEntryCreateSchema, \
    ErrorRecipeEntryCreateSchema, RecipeEntryUpdateSchema, RecipeStepCreateSchema, RecipeStepUpdateSchema, \
    RecipeStepUpdateErrorSchema, ReorderSchema, IngredientEntryListSchema, IngredientEntryCreateSchema, \
    IngredientErrorListSchema, PushSetupSchema, UnitEntryListSchema, IngredientAmountEntryCreateSchema, urlSchema
from pywebpush import WebPushException, webpush
router = Router()


@router.get('', response=List[RecipeEntryListSchema], auth=JWTAuth())
def list_recipes_entries(request):
    recipes = (Recipe.objects.filter(Q(public=True) |
               Q(user=request.user)).order_by('-pk'))
    for recipe in recipes:
        recipe.userStr = recipe.user.username
    return recipes


@router.post('/push/', auth=JWTAuth())
def setupPush(request, data: PushSetupSchema):
    data_dict = data.dict()
    registration_id = data_dict.get('registration_id')
    auth = data_dict.get('auth')
    p256dh = data_dict.get('p256dh')
    user = request.user
    name = data_dict.get('name')
    push_notification_obj = PushNotification.objects.get_or_create(
        registration_id=registration_id,
        auth=auth,
        p256dh=p256dh,
        user=user,
        name=name,
    )
    return {}


@router.get('/push/list/', response=List[PushNameSchema], auth=JWTAuth())
def getPushList(request,):
    user = request.user
    push_notification_objs = PushNotification.objects.filter(user=user)
    return push_notification_objs


@router.get('/units/', response=List[UnitEntryListSchema], auth=JWTAuth())
def get_units(request):
    units = Unit.objects.all()
    return units


@router.get('/ingredients/', response=List[IngredientEntryListSchema], auth=JWTAuth())
def list_ingredients_entries(request):
    ingredients = Ingredient.objects.filter(
        Q(public=True) | Q(user=request.user)).order_by('-pk')
    for ingredient in ingredients:
        ingredient.userStr = ingredient.user.username
    return ingredients


@router.post('/ingredients/search/', response=List[IngredientEntryListSchema], auth=JWTAuth())
def list_ingredients_entries(request, ingredientName: IngredientEntryCreateSchema):
    ingredients = Ingredient.objects.filter(Q(public=True) | Q(user=request.user),
                                            name__icontains=ingredientName.name).order_by('-pk')

    return ingredients[:10]


@router.post('/search/', response=List[RecipeEntryListSchema], auth=JWTAuth())
def recipe_search(request, recipeName: IngredientEntryCreateSchema):
    if recipeName.name:
        recipe = Recipe.objects.filter(Q(public=True) | Q(user=request.user),
                                       name__icontains=recipeName.name).order_by('-pk')
    else:
        recipe = Recipe.objects.filter(Q(public=True) | Q(user=request.user))
        recipe_list = list(recipe)
        sample_size = min(len(recipe_list), 5)
        recipe = sample(recipe_list, sample_size)
    return recipe[:5]


@router.delete('/ingredients/{entry_id}/', auth=JWTAuth(), response=List[IngredientEntryListSchema])
def delete_ingredients_entries(request, entry_id: int):
    ingredient = get_object_or_404(Ingredient, pk=entry_id)
    ingredient.delete()
    ingredients = Ingredient.objects.filter(
        Q(public=True) | Q(user=request.user)).order_by('-pk')
    for ingredient in ingredients:
        ingredient.userStr = ingredient.user.username
    return ingredients


@router.post('/push/set_default/', auth=JWTAuth())
def set_default_push_obj(request, data: IdSchema):
    user = request.user
    data_dict = data.dict()
    user_push_objs = PushNotification.objects.filter(user=request.user)
    for push_obj in user_push_objs:
        push_obj.current_active = False
        push_obj.save()
    push_obj = get_object_or_404(PushNotification, pk=data_dict['id'])

    if push_obj.user != user:
        return HttpResponse(status=404)

    push_obj.current_active = True
    push_obj.save()


@router.post('/push/current/', auth=JWTAuth())
def push_notification(request, post_data: PushNotificationInformation):
    push_obj = get_object_or_404(
        PushNotification, user=request.user, current_active=True)
    post_data_dict = post_data.dict()

    subscription_info = {
        'endpoint': push_obj.registration_id,
        'keys': {
            'auth': push_obj.auth,
            'p256dh': push_obj.p256dh,
        }
    }
    try:
        results = {"results": [
            {"original_registration_id": push_obj.registration_id}]}
        response = webpush(
            subscription_info=subscription_info,
            data=json.dumps(
                {'body': post_data_dict['body'], 'title': post_data_dict['title'], 'url': post_data_dict['url']}),
            vapid_private_key="private_key.pem",
            vapid_claims={'sub': 'mailto:peterturner99p@gmail.com'},
        )
        if response.ok:
            results["success"] = 1
        else:
            results["failure"] = 1
            results["results"][0]["error"] = response.content
        return results
    except WebPushException as e:
        if e.response is not None and e.response.status_code in [404, 410]:
            results["failure"] = 1
            results["results"][0]["error"] = e.message
            return results

    return HttpResponse({})


@router.delete('/push/{entry_id}/', auth=JWTAuth())
def delete_push_obj_entry(request, entry_id: int):
    push_obj = get_object_or_404(PushNotification, pk=entry_id)
    push_obj.delete()

    return ({})


@router.get('/push/{entry_id}/', auth=JWTAuth())
def push_notification(request, entry_id: int):
    push_obj = get_object_or_404(PushNotification, pk=entry_id)
    if not (request.user == push_obj.user):
        return {}
    message = "test message"
    subscription_info = {
        'endpoint': push_obj.registration_id,
        'keys': {
            'auth': push_obj.auth,
            'p256dh': push_obj.p256dh,
        }
    }
    try:
        results = {"results": [
            {"original_registration_id": push_obj.registration_id}]}
        response = webpush(
            subscription_info=subscription_info,
            data=json.dumps(
                {'body': message, 'title': 'test', 'url': 'urltest'}),
            vapid_private_key="private_key.pem",
            vapid_claims={'sub': 'mailto:peterturner99p@gmail.com'},
        )
        if response.ok:
            results["success"] = 1
        else:
            results["failure"] = 1
            results["results"][0]["error"] = response.content
        return results
    except WebPushException as e:
        if e.response is not None and e.response.status_code in [404, 410]:
            results["failure"] = 1
            results["results"][0]["error"] = e.message
            return results

    return HttpResponse({})


@router.post('/push/{entry_id}/', auth=JWTAuth())
def push_notification(request, entry_id: int, post_data: PushNotificationInformation):
    push_obj = get_object_or_404(PushNotification, pk=entry_id)
    post_data_dict = post_data.dict()
    if not (request.user == push_obj.user):
        return {}
    subscription_info = {
        'endpoint': push_obj.registration_id,
        'keys': {
            'auth': push_obj.auth,
            'p256dh': push_obj.p256dh,
        }
    }
    try:
        results = {"results": [
            {"original_registration_id": push_obj.registration_id}]}
        response = webpush(
            subscription_info=subscription_info,
            data=json.dumps(
                {'body': post_data_dict['body'], 'title': post_data_dict['title'], 'url': post_data_dict['url']}),
            vapid_private_key="private_key.pem",
            vapid_claims={'sub': 'mailto:peterturner99p@gmail.com'},
        )
        if response.ok:
            results["success"] = 1
        else:
            results["failure"] = 1
            results["results"][0]["error"] = response.content
        return results
    except WebPushException as e:
        if e.response is not None and e.response.status_code in [404, 410]:
            results["failure"] = 1
            results["results"][0]["error"] = e.message
            return results

    return HttpResponse({})


@router.post('/ingredients/', response={201: IngredientEntryListSchema, 400: IngredientErrorListSchema}, auth=JWTAuth())
def create_ingredient_entry(request, ingredient: IngredientEntryCreateSchema):
    data_dict = ingredient.dict()
    data_dict['user'] = request.user
    data_dict['name'] = data_dict['name'].capitalize()
    form = IngredientCreateForm(data_dict)
    if form.is_valid():
        ingredient = form.save()
        return 201, ingredient
    else:
        form_errors = json.loads(
            form.errors.as_json())
        errors_list = []
        for error_list in form_errors.values():
            error = error_list[0]
            errors_list.append(error.get('message', error.get('name')))
        error_dict = {'messages': errors_list}
        return 400, error_dict


@router.post(path='url/', auth=JWTAuth())
def import_url(request, data: urlSchema):
    data_dict = data.dict()
    url = data_dict.get('url')
    scraped_obj = scrape_me(url)
    obj_data = scraped_obj.schema.data
    recipe_name = obj_data.get('name')
    ingredients_and_amounts = obj_data.get('recipeIngredient')
    recipe_steps = obj_data.get('recipeInstructions')
    recipe_yield = obj_data.get('recipeYield')
    if recipe_yield:
        if isinstance(recipe_yield, list):
            recipe_yield = recipe_yield[0]
        elif isinstance(recipe_yield, int):
            pass
        else:
            recipe_yield = recipe_yield.split()[0]
    else:
        recipe_yield = 0

    recipe_description = obj_data.get('description')
    if not recipe_steps:
        return JsonResponse({'message': 'Recipe failed to import'})
    recipe_obj = Recipe.objects.get_or_create(
        user=request.user, name=recipe_name, description=recipe_description, source=url, serves=recipe_yield)[0]
    order = 0
    for step in recipe_steps:
        recipe_step_obj = RecipeStep.objects.get_or_create(
            recipe=recipe_obj, description=step.get('text'), order=order)[0]
        order = order + 1
    recipe_time = obj_data.get('totalTime')
    recipe_obj.duration = parse_duration(recipe_time).seconds // 60
    for ingredient in ingredients_and_amounts:

        parsed_ingredient = parse_ingredient(ingredient)
        ingredient_name = parsed_ingredient.name[0].text
        if not len(parsed_ingredient.amount) > 0:
            continue
        ingredient_amount_and_unit = parsed_ingredient.amount[0]
        if hasattr(ingredient_amount_and_unit, 'amounts'):
            amounts = ingredient_amount_and_unit.amounts
            for ingredient_amount_and_unit_sub in amounts:
                ingredient_amount = ingredient_amount_and_unit_sub.quantity
                ingredient_unit = ingredient_amount_and_unit_sub.unit if ingredient_amount_and_unit_sub.unit else 'unit(s)'
                unit_object = Unit.objects.get_or_create(name=ingredient_unit)
                ingredient = Ingredient.objects.filter(name=ingredient_name)
                if not ingredient.exists():
                    ingredient = Ingredient.objects.create(
                        name=ingredient_name, user=request.user, public=True)
                else:
                    ingredient = ingredient.first()
                if parsed_ingredient.comment:
                    details = parsed_ingredient.comment.text
                else:
                    details = None
                ingredient_and_amount_obj = IngredientAmount.objects.get_or_create(
                    ingredient=ingredient, amount=ingredient_amount, units=unit_object[0], user=request.user, public=True, details=details)
                recipe_obj.ingredients.add(ingredient_and_amount_obj[0])
        else:
            ingredient_amount = ingredient_amount_and_unit.quantity or 0
            ingredient_unit = ingredient_amount_and_unit.unit if ingredient_amount_and_unit.unit else 'unit(s)'
            unit_object = Unit.objects.get_or_create(name=ingredient_unit)
            ingredient = Ingredient.objects.filter(name=ingredient_name)
            if not ingredient.exists():
                ingredient = Ingredient.objects.create(
                    name=ingredient_name, user=request.user, public=True)
            else:
                ingredient = ingredient.first()
            if parsed_ingredient.comment:
                details = parsed_ingredient.comment.text
            else:
                details = None
            ingredient_and_amount_obj = IngredientAmount.objects.get_or_create(
                ingredient=ingredient, amount=ingredient_amount, units=unit_object[0], user=request.user, public=True, details=details)
            recipe_obj.ingredients.add(ingredient_and_amount_obj[0])
    recipe_obj.save()
    return JsonResponse({'message': 'Recipe imported successfully'})


@router.post('', response={201: RecipeEntryCreateSchema,
                           400: ErrorRecipeEntryCreateSchema}, auth=JWTAuth())
def create_recipes_entry(request, data: RecipeEntryCreateSchema):
    form = RecipeCreateForm(data.dict())
    if form.is_valid():
        cleaned_data = form.cleaned_data
        ingredients = cleaned_data.get('ingredients')
        recipe = Recipe.objects.get_or_create(
            name=cleaned_data.get('name'),
            description=cleaned_data.get('description'),
            user=request.user,
            duration=cleaned_data.get('duration'),
            public=cleaned_data.get('public'),
        )[0]
        recipe.ingredients.add(*ingredients)
        recipe.save()
        return 201, recipe
    else:
        form_errors = json.loads(
            form.errors.as_json())
        return 400, form_errors


@router.get("/{entry_id}/", response=RecipeEntryDetailSchema, auth=JWTAuth())
def get_recipes_entry(request, entry_id: int):
    obj = get_object_or_404(Recipe, pk=entry_id)
    recipeSteps = obj.recipestep_set.all().order_by('order')
    obj.recipestep_set.set(recipeSteps)
    return obj


@router.post("/{entry_id}/ingredient/", response={200: RecipeEntryDetailSchema, 400: IngredientErrorListSchema},
             auth=JWTAuth())
def get_recipes_entry(request, entry_id: int, data: IngredientAmountEntryCreateSchema):
    obj = get_object_or_404(Recipe, pk=entry_id)
    data_dict = data.dict()
    data_dict['user'] = request.user
    ingredient_name = data_dict.get('name')
    unit = Unit.objects.get(pk=data_dict.get('unit_id'))
    data_dict['units'] = unit
    ingredient = Ingredient.objects.get_or_create(
        user=request.user, name=ingredient_name)[0]
    form = IngredientAmountCreateForm(data_dict)
    if form.is_valid():
        cleaned_data = form.cleaned_data
        ingredient_amount = IngredientAmount.objects.get_or_create(
            amount=cleaned_data.get('amount'), ingredient=ingredient, units=cleaned_data.get('units'),
            user=cleaned_data.get('user')
        )[0]
        obj.ingredients.add(ingredient_amount)
        return obj
    else:
        form_errors = json.loads(
            form.errors.as_json())
        errors_list = []
        for error_list in form_errors.values():
            error = error_list[0]
            errors_list.append(error.get('message', error.get('name')))
        error_dict = {'messages': errors_list}
        return 400, error_dict


@router.put("/{entry_id}/", response=RecipeEntryDetailSchema, auth=JWTAuth())
def update_recipes_entry(request, entry_id: int, data: RecipeEntryUpdateSchema):
    obj = get_object_or_404(Recipe, pk=entry_id)

    for attr, value in data.dict().items():
        if value is not None:
            setattr(obj, attr, value)
    obj.save()
    return obj


@router.put("/{entry_id}/step/{step_id}/", response={200: RecipeEntryDetailSchema,
                                                     400: RecipeStepUpdateErrorSchema}, auth=JWTAuth())
def update_recipe_step_entry(request, entry_id: int, step_id: int, data: RecipeStepUpdateSchema):
    obj = get_object_or_404(RecipeStep, pk=step_id)
    # for attr, value in data.dict().items():
    #     if value is not None:
    #         setattr(obj, attr, value)
    # obj.save()
    form = RecipeStepUpdateForm(data.dict())
    if form.is_valid():
        cleaned_data = form.cleaned_data
        for attr, value in cleaned_data.items():
            if value != None:
                setattr(obj, attr, value)
        obj.save()
        return 200, obj.recipe
    else:
        form_error_data = form.errors
        errors = []
        response_data = {f: [error for error in e]
                         for f, e in form_error_data.items()}

        return 400, response_data


@router.post('/{entry_id}/step/', response=RecipeEntryDetailSchema, auth=JWTAuth())
def create_recipe_step(request, entry_id: int, data: RecipeStepCreateSchema):
    dataDict = data.dict()
    recipeObj = get_object_or_404(Recipe, pk=entry_id)
    existing_recipe_steps = recipeObj.recipestep_set.all()
    max_order_number = existing_recipe_steps.aggregate(Max('order'))[
        'order__max']

    RecipeStep.objects.create(recipe=recipeObj, shortDesc=dataDict.get('shortDesc', ''),
                              description=dataDict.get('description', ''), duration=dataDict.get('duration', 0),
                              order=max_order_number + 1)

    return recipeObj


@router.post('/{entry_id}/reorder/', response=RecipeEntryDetailSchema, auth=JWTAuth())
def reorder_recipe_steps(request, entry_id: int, data: ReorderSchema):
    recipe_obj = get_object_or_404(Recipe, pk=entry_id)
    recipe_steps = recipe_obj.recipestep_set.all()
    for step in recipe_steps:
        step.order = None
        step.save()
    for step_data in data.dict().get('ordering'):
        recipe_step = RecipeStep.objects.get(pk=step_data[0])
        recipe_step.order = step_data[1] + 1
        recipe_step.save()
    return recipe_obj


@router.delete('/{recipe_id}/{ing_amount_id}/delete/', response=RecipeEntryDetailSchema, auth=JWTAuth())
def delete_recipe_step(request, recipe_id: int, ing_amount_id: int):
    recipe_obj = get_object_or_404(Recipe, pk=recipe_id)
    ingredient_amount_obj = get_object_or_404(
        IngredientAmount, pk=ing_amount_id)
    recipe_obj.ingredients.remove(ingredient_amount_obj)
    recipe_obj.save()
    return recipe_obj
