from django.shortcuts import render
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from datetime import datetime, timezone, timedelta

def hello_world(request):
    return render(request, 'test.html', {
            'current_time': str(datetime.now(timezone(timedelta(hours=+8)))),
            })

import jkforum as jkf

def jkforum(request):
    zone = int(request.GET.get('zone', 0))
    max_count = int(request.GET.get('count', 10))
    show = bool(request.GET.get('show', False))
    title, body = jkf.request(zone, max_count)
    return render(request, 'jkf.html', {
            'title': title,
            'body': mark_safe(body),
            })

def jkforum_select(request):
    zone = int(request.GET.get('zone', 0))
    max_count = int(request.GET.get('count', 10))
    is_found = bool(request.GET.get('is_found', True))
    show = bool(request.GET.get('show', False))
    title, body = jkf.select(zone, max_count, is_found, show)
    return render(request, 'jkf_select.html', {
            'title': title,
            'body': mark_safe(body),
            })

def jkforum_delete(request):
    tid = request.GET.get('tid', '')
    if len(tid) > 0:
        del_msg = jkf.delete(tid)
    else:
        del_msg = ''
    return render(request, 'test.html', {
            'current_time': str(datetime.now(timezone(timedelta(hours=+8)))) + ' MSG=' + del_msg,
            })
    
def jkforum_deleteAll(request):
    jkf.deleteAll()
    return render(request, 'test.html', {
            'current_time': str(datetime.now(timezone(timedelta(hours=+8)))),
            })
    
def jkforum_tag(request):
    zone = int(request.GET.get('zone', 0))
    tag = request.GET.get('tag', '')
    msg = jkf.tag(zone, tag)
    return render(request, 'test.html', {
            'current_time': str(datetime.now(timezone(timedelta(hours=+8)))) + ' MSG=' + msg,
            })
    
def jkforum_keep(request):
    tid = request.GET.get('tid', '')
    status = int(request.GET.get('status', 0))
    if len(tid) > 0:
        msg = jkf.keep(tid, status)
    else:
        msg = ''
    return render(request, 'test.html', {
            'current_time': str(datetime.now(timezone(timedelta(hours=+8)))) + ' MSG=' + msg,
            })
    
def sugar(request):
    return render(request, 'test.html', {
            'current_time': str(datetime.now(timezone(timedelta(hours=+8)))),
            })
