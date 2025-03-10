from typing import List

from ninja import Schema, Field

from firstProjectApp.schemas import RecipeEntryDetailSchema


class SearchSchema(Schema):
    search: str = ""


class MenuListSchema(Schema):
    recipeEntry: RecipeEntryDetailSchema = Field(..., alias='recipe')
    type: str = Field(None, alias='get_type_display')
    id: int


class MenuListAndDateSchema(Schema):
    recipeEntry: RecipeEntryDetailSchema = Field(..., alias='recipe')
    id: int
    date: str = Field(None, alias='get_date_str')


class MealAddSchema(Schema):
    recipe: str
    date: str = ""
    time: str


class MealUpdateSchema(Schema):
    recipe: str = ""
    date: str = ""
    time: str = ""


class errorSchema(Schema):
    messages: List[str] = []
