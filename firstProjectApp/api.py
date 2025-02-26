import json
from typing import List
from django.db.models import Max
from django.db.models import Q
from ninja import Router
from .schemas import RecipeEntryListSchema, RecipeEntryDetailSchema, RecipeEntryCreateSchema, \
    ErrorRecipeEntryCreateSchema, RecipeEntryUpdateSchema, RecipeStepCreateSchema, RecipeStepUpdateSchema, \
    RecipeStepUpdateErrorSchema, ReorderSchema, IngredientEntryListSchema, IngredientEntryCreateSchema, \
    IngredientErrorListSchema, UnitEntryListSchema, IngredientAmountEntryCreateSchema
from .models import Recipe, RecipeStep, Ingredient, Unit, IngredientAmount
from ninja_jwt.authentication import JWTAuth
from django.shortcuts import get_object_or_404
from .forms import RecipeCreateForm, RecipeStepUpdateForm, IngredientCreateForm, IngredientAmountCreateForm

router = Router()


@router.get('', response=List[RecipeEntryListSchema], auth=JWTAuth())
def list_recipes_entries(request):
    recipes = (Recipe.objects.filter(Q(public=True) | Q(user=request.user)).order_by('-pk'))
    for recipe in recipes:
        recipe.userStr = recipe.user.username
    return recipes


@router.get('/units/', response=List[UnitEntryListSchema], auth=JWTAuth())
def get_units(request):
    units = Unit.objects.all()
    return units


@router.get('/ingredients/', response=List[IngredientEntryListSchema], auth=JWTAuth())
def list_ingredients_entries(request):
    ingredients = Ingredient.objects.filter(Q(public=True) | Q(user=request.user)).order_by('-pk')
    for ingredient in ingredients:
        ingredient.userStr = ingredient.user.username
    return ingredients


@router.post('/ingredients/search/', response=List[IngredientEntryListSchema], auth=JWTAuth())
def list_ingredients_entries(request, ingredientName: IngredientEntryCreateSchema):
    ingredients = Ingredient.objects.filter(Q(public=True) | Q(user=request.user),
                                            name__icontains=ingredientName.name).order_by('-pk')

    return ingredients[:10]


@router.delete('/ingredients/{entry_id}/', auth=JWTAuth(), response=List[IngredientEntryListSchema])
def delete_ingredients_entries(request, entry_id: int):
    ingredient = get_object_or_404(Ingredient, pk=entry_id)
    ingredient.delete()
    ingredients = Ingredient.objects.filter(Q(public=True) | Q(user=request.user)).order_by('-pk')
    for ingredient in ingredients:
        ingredient.userStr = ingredient.user.username
    return ingredients


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


@router.post('', response={201: RecipeEntryCreateSchema,
                           400: ErrorRecipeEntryCreateSchema}, auth=JWTAuth())
def create_recipes_entry(request, data: RecipeEntryCreateSchema):
    form = RecipeCreateForm(data.dict())
    if form.is_valid():
        cleaned_data = form.cleaned_data
        ingredients = cleaned_data.get('ingredients')
        recipe = Recipe.objects.create(
            name=cleaned_data.get('name'),
            description=cleaned_data.get('description'),
            user=request.user,
            duration=cleaned_data.get('duration'),
            public=cleaned_data.get('public'),
        )
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
    ingredient = Ingredient.objects.get_or_create(user=request.user, name=ingredient_name)[0]
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
        response_data = {f: [error for error in e] for f, e in form_error_data.items()}

        return 400, response_data


@router.post('/{entry_id}/step/', response=RecipeEntryDetailSchema, auth=JWTAuth())
def create_recipe_step(request, entry_id: int, data: RecipeStepCreateSchema):
    dataDict = data.dict()
    recipeObj = get_object_or_404(Recipe, pk=entry_id)
    existing_recipe_steps = recipeObj.recipestep_set.all()
    max_order_number = existing_recipe_steps.aggregate(Max('order'))['order__max']

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
