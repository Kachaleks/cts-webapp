# bot/models.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class BotOrder:
    user_id: int
    chat_id: int

    distance: Optional[str] = None      # расстояние от города
    quality: Optional[str] = None       # обычные / 4K
    location: Optional[str] = None      # улица / помещение / оба
    camera_count: Optional[str] = None  # количество (строкой — может быть "5-10")
    storage: Optional[str] = None       # срок хранения

    client_name: Optional[str] = None
    client_phone: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)