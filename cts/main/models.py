from django.db import models


class Camera(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    name = models.CharField('Название камеры', max_length=100)
    description = models.CharField('Описание камеры', max_length=200, null=True, blank=True)
    price = models.IntegerField('Цена камеры')
    picture = models.ImageField(
        'Фото камеры',
        upload_to='camera_images/',
        blank=True,
        null=True
    )
    resolution = models.IntegerField('Разрешение', default=2)
    type = models.CharField('Тип', max_length=10, default='Купольная')
    night_vision_technology = models.CharField('Ночное видение', max_length=6, default='Color')
    connection_type = models.CharField('Тип подключения', max_length=10, default='Провод')
    lens = models.CharField('Объектив', max_length=15, default='')
    has_micro = models.BooleanField('Микрофон', default=False)
    has_dynamic = models.BooleanField('Динамик', default=False)
    has_zoom = models.BooleanField('Зум', default=False)
    has_people_analytics = models.BooleanField('Аналитика: люди', default=False)
    has_cars_analytics = models.BooleanField('Аналитика: транспорт', default=False)
    has_special_cars_analytics = models.BooleanField('Аналитика: спецтехника', default=False)
    is_available = models.BooleanField('В наличии', default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Камера'
        verbose_name_plural = 'Камеры'


class CableSettings(models.Model):
    price_per_meter = models.IntegerField('Стоимость метра кабеля (руб)', default=125)
    is_active = models.BooleanField('Активно', default=True)

    def save(self, *args, **kwargs):
        if self.is_active:
            CableSettings.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Кабель: {self.price_per_meter} руб/м"

    class Meta:
        verbose_name = 'Настройка кабеля'
        verbose_name_plural = 'Настройки кабеля'