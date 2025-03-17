from ninja import schema, Field
from typing import Optional
from datetime import datetime
from typing import List


class RecipeEntryCreateSchema(schema.Schema):
    name: str
    description: str = ""
    duration: Optional[int] = None
    ingredients: list = None
    public: bool = False


class RecipeEntryUpdateSchema(schema.Schema):
    name: str = None
    description: str = None
    duration: Optional[int] = None
    ingredients: list = None
    public: bool = None


class ErrorRecipeEntryCreateSchema(schema.Schema):
    name: str
    description: str = ""
    duration: Optional[int] = None
    ingredients: list = None
    public: bool = False


class RecipeEntryListSchema(schema.Schema):
    id: int
    name: str
    description: str = ""
    duration: Optional[int] = None
    userStr: str = ""
    public: bool = False

class IngredientEntryListSchema(schema.Schema):
    id: int
    name: str = ''


class IngredientEntryDetailsSchema(schema.Schema):
    id: int
    name: str = ''
    calories: Optional[int] = None


class IngredientEntryCreateSchema(schema.Schema):
    name: str


class IngredientErrorListSchema(schema.Schema):
    messages: List[str] = []


class RecipeStepDetailSchema(schema.Schema):
    id: int
    order: int
    description: str
    duration: Optional[int] = None
    shortDesc: Optional[str] = ""


class RecipeStepCreateSchema(schema.Schema):
    shortDesc: str = ""
    description: str = ""
    duration: Optional[int] = None


class RecipeStepUpdateSchema(schema.Schema):
    order: Optional[int] = None
    shortDesc: str = None
    description: str = None
    duration: Optional[int] = None
    public: Optional[bool] = None


class IngredientAmountDetailSchema(schema.Schema):
    id: int
    amount: float
    units_str: str
    name: str
    details: Optional[str] = ""

class urlSchema(schema.Schema):
    url: str


class RecipeEntryDetailSchema(schema.Schema):
    id: int
    name: str
    description: str = ""
    duration: Optional[int]
    public: bool
    ingredients: List[IngredientAmountDetailSchema] = Field(..., alias='ingredients')
    recipeSteps: List[RecipeStepDetailSchema] = Field(..., alias='recipestep_set')


class RecipeStepUpdateErrorSchema(schema.Schema):
    shortDesc: List[str] = []
    description: List[str] = []
    duration: List[str] = []


class ReorderSchema(schema.Schema):
    ordering: List[List[int]] = [[]]


class UnitEntryListSchema(schema.Schema):
    id: int
    name: str = ""


class IngredientAmountEntryCreateSchema(schema.Schema):
    amount: int
    name: str = ""
    unit_id: int
