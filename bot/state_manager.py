# bot/state_manager.py
"""
Менеджер состояний пользователей
"""
import logging
from enum import Enum
from typing import Dict, Optional
from models import BotOrder

logger = logging.getLogger(__name__)


class State(Enum):
    # Фильтры
    START               = "start"
    FILTER_TYPE         = "filter_type"           # тип камеры
    FILTER_CONNECTION   = "filter_connection"      # улица/помещение
    FILTER_RESOLUTION   = "filter_resolution"      # разрешение
    FILTER_NIGHT_VISION = "filter_night_vision"    # ночное видение
    FILTER_OPTIONS      = "filter_options"         # доп. опции (микро, зум, аналитика)

    # Выбор камер
    CAMERA_LIST         = "camera_list"            # показываем список камер
    CAMERA_QUANTITY     = "camera_quantity"        # ввод количества камер
    CAMERA_CABLE        = "camera_cable"           # ввод метров кабеля
    CART_VIEW           = "cart_view"              # просмотр корзины

    # Оформление заявки
    WAITING_NAME        = "waiting_name"
    WAITING_PHONE       = "waiting_phone"
    CONFIRM             = "confirm"
    COMPLETED           = "completed"


class StateManager:
    def __init__(self):
        self._states: Dict[int, State] = {}
        self._orders: Dict[int, BotOrder] = {}
        self._history: Dict[int, list] = {}

    def get_state(self, user_id: int) -> State:
        return self._states.get(user_id, State.START)

    def set_state(self, user_id: int, state: State):
        old = self.get_state(user_id)
        self._states[user_id] = state
        self._history.setdefault(user_id, []).append(state)
        logger.debug(f"User {user_id}: {old.value} → {state.value}")

    def get_order(self, user_id: int, chat_id: int) -> BotOrder:
        if user_id not in self._orders:
            self._orders[user_id] = BotOrder(user_id=user_id, chat_id=chat_id)
        return self._orders[user_id]

    def reset(self, user_id: int):
        self._states.pop(user_id, None)
        self._orders.pop(user_id, None)
        self._history.pop(user_id, None)
        logger.info(f"User {user_id} state reset")

    def go_back(self, user_id: int) -> Optional[State]:
        history = self._history.get(user_id, [])
        if len(history) > 1:
            history.pop()  # убираем текущий
            prev = history[-1]
            self._states[user_id] = prev
            return prev
        return None