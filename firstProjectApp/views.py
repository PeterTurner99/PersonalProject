from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.

def simpleApiView(request):
    return JsonResponse({'test': 'test1'})


def simpleView(request):
    return render(request, 'firstProjectApp/test.html', context={})
