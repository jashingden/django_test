from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime

import mysys
import sys
sys.path.append(mysys.mydir + 'Python')

def hello_world(request):
    return render(request, 'test.html', {
            'current_time': str(datetime.now()),
            })

import jkforum as jkf

def jkforum(request):
    if 'zone' in request.GET:
        zone = request.GET['zone']
        count = request.GET.get('count', 10)
        jkf.zone = zone
        jkf.max_count = count
        return HttpResponse(jkf.run())
    else:
        return render(request, 'jkf.html', {})
