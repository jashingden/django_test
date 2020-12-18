from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime

def hello_world(request):
    return render(request, 'test.html', {
            'current_time': str(datetime.now()),
            })

import jkforum as jkf

def jkforum(request):
    zone = int(request.GET.get('zone', 0))
    max_count = int(request.GET.get('count', 10))
    title, output = jkf.request(zone, max_count)
    return HttpResponse(output)
