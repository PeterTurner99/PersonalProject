from ninja import Schema
from ninja_jwt.controller import NinjaJWTDefaultController
from ninja_jwt.authentication import JWTAuth
from ninja_extra import NinjaExtraAPI
from ninja.errors import ValidationError
from django.http import Http404

api = NinjaExtraAPI()
api.register_controllers(NinjaJWTDefaultController)
api.add_router('/recipes/', 'firstProjectApp.api.router')


class UserSchema(Schema):
    username: str
    is_authenticated: bool
    email: str = ""


@api.get('/hello')
def hello(request):
    print(request)
    return {"Hello World!": "Hello World!"}


@api.get('/me', response=UserSchema, auth=JWTAuth())
def me(request):
    return request.user


@api.exception_handler(ValidationError)
def custom_validation_errors(request, exc):
    print(exc.errors)  # <--------------------- !!!!
    return api.create_response(request, {"detail": exc.errors}, status=422)


@api.exception_handler(Http404)
def custom_404_errors(request, exc):
    return api.create_response(request, {"detail": "Not Found"}, status=404)
