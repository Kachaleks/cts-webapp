# bot/models.py
"""
Модели данных для заказа через бота
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict


@dataclass
class CartItem:
    """Одна позиция в корзине: камера + количество + метры кабеля"""
    camera_id: int
    camera_name: str
    camera_price: int
    quantity: int = 1
    cable_meters: int = 0

    @property
    def cameras_total(self) -> int:
        return self.camera_price * self.quantity

    @property
    def cable_total(self) -> int:
        return 0  # считается отдельно с учётом цены за метр

    def to_dict(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "camera_price": self.camera_price,
            "quantity": self.quantity,
            "cable_meters": self.cable_meters,
        }


@dataclass
class BotOrder:
    """Заказ из бота"""
    user_id: int
    chat_id: int

    # Фильтры (шаги 1-5)
    filter_type: Optional[str] = None               # тип камеры
    filter_connection: Optional[str] = None          # улица/помещение
    filter_resolution: Optional[int] = None          # разрешение
    filter_night_vision: Optional[str] = None        # ночное видение
    filter_has_people_analytics: bool = False
    filter_has_cars_analytics: bool = False
    filter_has_micro: bool = False
    filter_has_zoom: bool = False

    # Корзина
    cart: List[CartItem] = field(default_factory=list)

    # Текущая выбранная камера (для шага ввода кол-ва и метров)
    pending_camera_id: Optional[int] = None

    # Контакты клиента
    client_name: Optional[str] = None
    client_phone: Optional[str] = None

    # Метаданные
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def get_active_filters(self) -> dict:
        """Возвращает только заполненные фильтры для запроса к БД"""
        f = {}
        if self.filter_type:
            f["type"] = self.filter_type
        if self.filter_connection:
            f["connection_type"] = self.filter_connection
        if self.filter_resolution:
            f["resolution"] = self.filter_resolution
        if self.filter_night_vision:
            f["night_vision_technology"] = self.filter_night_vision
        if self.filter_has_people_analytics:
            f["has_people_analytics"] = True
        if self.filter_has_cars_analytics:
            f["has_cars_analytics"] = True
        if self.filter_has_micro:
            f["has_micro"] = True
        if self.filter_has_zoom:
            f["has_zoom"] = True
        return f

    def add_to_cart(self, camera_id: int, camera_name: str,
                    camera_price: int, quantity: int, cable_meters: int = 0):
        """Добавить или обновить позицию в корзине"""
        for item in self.cart:
            if item.camera_id == camera_id:
                item.quantity = quantity
                item.cable_meters = cable_meters
                return
        self.cart.append(CartItem(
            camera_id=camera_id,
            camera_name=camera_name,
            camera_price=camera_price,
            quantity=quantity,
            cable_meters=cable_meters,
        ))

    def remove_from_cart(self, camera_id: int):
        self.cart = [i for i in self.cart if i.camera_id != camera_id]

    def get_cart_item(self, camera_id: int) -> Optional[CartItem]:
        for item in self.cart:
            if item.camera_id == camera_id:
                return item
        return None

    def calculate_total(self, cable_price_per_meter: int) -> Dict[str, int]:
        """Подсчёт итогов"""
        cameras_total = sum(i.cameras_total for i in self.cart)
        total_cable_meters = sum(i.cable_meters * i.quantity for i in self.cart)
        cable_total = total_cable_meters * cable_price_per_meter
        # Монтаж = цена кабеля (можно задать отдельно, пока равно стоимости кабеля)
        installation_total = cable_total
        grand_total = cameras_total + cable_total + installation_total

        return {
            "cameras_total": cameras_total,
            "cable_meters": total_cable_meters,
            "cable_total": cable_total,
            "installation_total": installation_total,
            "grand_total": grand_total,
        }

    def is_cart_empty(self) -> bool:
        return len(self.cart) == 0