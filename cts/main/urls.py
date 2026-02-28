from django.urls import path
from . import views

urlpatterns = [
    path("", views.calculator),
    path("send-order/", views.send_order),   #endpoint для отправки заказа с калькулятора
]