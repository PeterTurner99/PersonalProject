from django.urls import path
import firstProjectApp.views as views

urlpatterns = [
    path('', views.simpleApiView, name='test'),
]
