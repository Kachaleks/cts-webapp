# bot/state_manager.py
import logging
from enum import Enum
from typing import Dict, Optional
from models import BotOrder

logger = logging.getLogger(__name__)


class State(Enum):
    START            = "start"
    STEP_DISTANCE    = "step_distance"     # 1. Расстояние от города
    STEP_QUALITY     = "step_quality"      # 2. Обычные или 4K
    STEP_LOCATION    = "step_location"     # 3. Улица / помещение / оба
    STEP_COUNT       = "step_count"        # 4. Количество камер (текст)
    STEP_STORAGE     = "step_storage"      # 5. Срок хранения
    WAITING_NAME     = "waiting_name"      # 6. Имя
    WAITING_PHONE    = "waiting_phone"     # 7. Телефон
    CONFIRM          = "confirm"
    COMPLETED        = "completed"


class StateManager:
    def __init__(self):
        self._states: Dict[int, State] = {}
        self._orders: Dict[int, BotOrder] = {}
        self._history: Dict[int, list] = {}

    def get_state(self, user_id: int) -> State:
        return self._states.get(user_id, State.START)

    def set_state(self, user_id: int, state: State):
        self._states[user_id] = state
        self._history.setdefault(user_id, []).append(state)

    def get_order(self, user_id: int, chat_id: int) -> BotOrder:
        if user_id not in self._orders:
            self._orders[user_id] = BotOrder(user_id=user_id, chat_id=chat_id)
        return self._orders[user_id]

    def reset(self, user_id: int):
        self._states.pop(user_id, None)
        self._orders.pop(user_id, None)
        self._history.pop(user_id, None)

    def go_back(self, user_id: int) -> Optional[State]:
        history = self._history.get(user_id, [])
        if len(history) > 1:
            history.pop()
            prev = history[-1]
            self._states[user_id] = prev
            return prev
        return None