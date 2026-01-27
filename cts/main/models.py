from django.db import models

class Camera(models.Model):
    id = (models.AutoField(primary_key=True, auto_created=True))
    name = models.CharField('Название камеры', max_length=100)
    price = models.IntegerField('Цена камеры')
    picture = models.ImageField('Фото камеры')
    resolution = models.IntegerField('Разрешение', default=2)
    type = models.CharField(max_length=10, default='Купольная')
    night_vision_technology = models.CharField(max_length=6, default='Color')
    connection_type = models.CharField(max_length=10, default='Провод')
    has_micro = models.BooleanField(default=False)
    has_dynamic = models.BooleanField(default=False)
    lens = models.CharField(max_length=15, default='Zoom')
    analytics = models.CharField(max_length=30, default='Человек')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Камера'
        verbose_name_plural = 'Камеры'


