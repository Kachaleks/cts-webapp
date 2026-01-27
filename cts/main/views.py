from django.shortcuts import render
from django.http import HttpResponse
from .models import Camera


def calculator(request):
    cameras = Camera.objects.all()
    resolutions = cameras.values_list('resolution', flat=True).distinct()
    types = cameras.values_list('type', flat=True).distinct()
    night_vision_technologies = cameras.values_list('night_vision_technology', flat=True).distinct()
    connection_types = cameras.values_list('connection_type', flat=True).distinct()
    lens = cameras.values_list('lens', flat=True).distinct()
    analytics = cameras.values_list('analytics', flat=True).distinct()

    tables = {
                    'cameras': cameras,
                    'resolutions': resolutions,
                    'types': types,
                    'night_vision_technologies' : night_vision_technologies,
                    'connection_types': connection_types,
                    'lens': lens,
                    'analytics': analytics}

    return render(request, 'main/calculator.html', context=tables)




