from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import Camera, CableSettings



def calculator(request):

    # Обычный запрос - показываем главную страницу
    cameras = Camera.objects.all()
    cables_settings = CableSettings.objects.filter(is_active=True).first()

    # Получаем уникальные значения для фильтров
    resolutions = cameras.values_list('resolution', flat=True).distinct()
    types = cameras.values_list('type', flat=True).distinct()
    night_vision_technologies = cameras.values_list('night_vision_technology', flat=True).distinct()
    connection_types = cameras.values_list('connection_type', flat=True).distinct()
    lens = cameras.values_list('lens', flat=True).distinct()
    cable_price_per_meter = cables_settings.price_per_meter

    # Если AJAX запрос
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Простая фильтрация
        if 'resolution' in request.GET:
            cameras = cameras.filter(resolution=int(request.GET['resolution']))
        if 'type' in request.GET:
            cameras = cameras.filter(type=request.GET['type'])
        if 'night_vision_technology' in request.GET:
            cameras = cameras.filter(night_vision_technology=request.GET['night_vision_technology'])
        if 'connection_types' in request.GET:
            cameras = cameras.filter(connection_typ=request.GET['connection_types'])
        if 'lens' in request.GET:
            lens_values = request.GET.getlist('lens')
            if lens_values:
                # Используем __in для поиска точных совпадений
                cameras = cameras.filter(lens__in=lens_values)

        # ИСПРАВЛЕНИЕ: Проверяем значение булевых полей
        if 'has_zoom' in request.GET:
            # Преобразуем строку в булево значение
            has_zoom_value = request.GET['has_zoom'].lower() == 'true'
            cameras = cameras.filter(has_zoom=has_zoom_value)

        if 'has_people_analytics' in request.GET:
            cameras = cameras.filter(has_people_analytics=True)
        if 'has_cars_analytics' in request.GET:
            cameras = cameras.filter(has_cars_analytics=True)
        if 'has_special_cars_analytics' in request.GET:
            cameras = cameras.filter(has_special_cars_analytics=True)

            # ФИЛЬТРАЦИЯ ПО МИКРОФОНУ И ДИНАМИКУ (ключевое изменение!)
        if 'has_micro' in request.GET:
            cameras = cameras.filter(has_micro=True)
        if 'has_dynamic' in request.GET:
            cameras = cameras.filter(has_dynamic=True)




        # Возвращаем простой JSON
        data = {
            'cameras': [
                {
                    'id': c.id,
                    'name': c.name,
                    'type': c.type,
                    'resolution': c.resolution,
                    'connection_type': c.connection_type,
                    'price': c.price,
                    'picture': c.picture.path if c.picture else '',
                    'has_micro': c.has_micro,
                    'has_zoom' : c.has_zoom,
                    'has_dynamic': c.has_dynamic,

                }
                for c in cameras
            ],
            'cable_price': cable_price_per_meter,
        }
        return JsonResponse(data)

    # Контекст для шаблона
    context = {
                    'cameras': cameras,
                    'resolutions': resolutions,
                    'types': types,
                    'night_vision_technologies' : night_vision_technologies,
                    'connection_types': connection_types,
                    'lens': lens,
                    'installation_price': cable_price_per_meter,  # Модель с ценой монтажа

    }

    # ЕДИНСТВЕННЫЙ return для обычного запроса
    return render(request, 'main/calculator.html', context)




