from django.shortcuts import render
from django.http import HttpResponse

def ajax_test(request):
    return render(request, 'ajax_test.html')
