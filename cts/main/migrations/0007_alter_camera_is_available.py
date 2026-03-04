# Generated manually — добавлены недостающие поля

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0006_alter_camera_picture"),
    ]

    operations = [
        migrations.AddField(
            model_name="camera",
            name="description",
            field=models.CharField(
                blank=True, max_length=200, null=True,
                verbose_name="Описание камеры"
            ),
        ),
        migrations.AddField(
            model_name="camera",
            name="has_people_analytics",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="camera",
            name="has_cars_analytics",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="camera",
            name="has_special_cars_analytics",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="camera",
            name="has_zoom",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="camera",
            name="is_available",
            field=models.BooleanField(default=True, verbose_name="В наличии"),
        ),
        # Убираем старое поле analytics (заменено на булевые поля)
        migrations.RemoveField(
            model_name="camera",
            name="analytics",
        ),
        # CableSettings модель
        migrations.CreateModel(
            name="CableSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("price_per_meter", models.IntegerField(default=125, verbose_name="Стоимость метра кабеля (руб)")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активно")),
            ],
            options={
                "verbose_name": "Настройка кабеля",
                "verbose_name_plural": "Настройки кабеля",
            },
        ),
    ]