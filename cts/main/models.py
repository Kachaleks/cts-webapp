from django.db import models

class Camera(models.Model):
    id = (models.AutoField(primary_key=True, auto_created=True))
    name = models.CharField('Название камеры', max_length=100)
    description = models.CharField('Описание камеры', max_length=200, null=True, blank=True)
    price = models.IntegerField('Цена камеры')
    picture = models.ImageField(
        'Фото камеры',
        upload_to='main/static/main/img/camera_images',  # папка для сохранения
        blank=True,  # необязательное в формах
        null=True  # может быть NULL в БД
    )
    resolution = models.IntegerField('Разрешение', default=2)
    type = models.CharField(max_length=10, default='Купольная')
    night_vision_technology = models.CharField(max_length=6, default='Color')
    connection_type = models.CharField(max_length=10, default='Провод')
    has_micro = models.BooleanField(default=False)
    has_dynamic = models.BooleanField(default=False)
    lens = models.CharField(max_length=15, default='')
    has_zoom = models.BooleanField(default=False)
    has_people_analytics = models.BooleanField(default=False)
    has_cars_analytics = models.BooleanField(default=False)
    has_special_cars_analytics = models.BooleanField(default=False)


    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Камера'
        verbose_name_plural = 'Камеры'


