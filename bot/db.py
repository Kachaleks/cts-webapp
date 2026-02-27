# bot/db.py
"""
Прямое чтение камер из Django SQLite (только чтение, отдельный пользователь не нужен для SQLite)
"""
import sqlite3
import logging
from dataclasses import dataclass
from typing import List, Optional
from bot.config import DJANGO_DB_PATH

logger = logging.getLogger(__name__)


@dataclass
class Camera:
    id: int
    name: str
    price: int
    resolution: int
    type: str
    night_vision_technology: str
    connection_type: str
    lens: str
    has_zoom: bool
    has_micro: bool
    has_dynamic: bool
    has_people_analytics: bool
    has_cars_analytics: bool
    has_special_cars_analytics: bool
    picture: str = ""
    description: str = ""


@dataclass
class CableSettings:
    price_per_meter: int


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DJANGO_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_cameras(filters: dict = None) -> List[Camera]:
    """Получить камеры с опциональной фильтрацией"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM main_camera WHERE 1=1"
        params = []

        if filters:
            if filters.get("type"):
                query += " AND type = ?"
                params.append(filters["type"])
            if filters.get("resolution"):
                query += " AND resolution = ?"
                params.append(filters["resolution"])
            if filters.get("night_vision_technology"):
                query += " AND night_vision_technology = ?"
                params.append(filters["night_vision_technology"])
            if filters.get("connection_type"):
                query += " AND connection_type = ?"
                params.append(filters["connection_type"])
            if filters.get("has_zoom") is not None:
                query += " AND has_zoom = ?"
                params.append(1 if filters["has_zoom"] else 0)
            if filters.get("has_micro"):
                query += " AND has_micro = 1"
            if filters.get("has_dynamic"):
                query += " AND has_dynamic = 1"
            if filters.get("has_people_analytics"):
                query += " AND has_people_analytics = 1"
            if filters.get("has_cars_analytics"):
                query += " AND has_cars_analytics = 1"
            if filters.get("has_special_cars_analytics"):
                query += " AND has_special_cars_analytics = 1"

        query += " ORDER BY price ASC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        cameras = []
        for row in rows:
            cameras.append(Camera(
                id=row["id"],
                name=row["name"],
                price=row["price"],
                resolution=row["resolution"],
                type=row["type"],
                night_vision_technology=row["night_vision_technology"],
                connection_type=row["connection_type"],
                lens=row["lens"],
                has_zoom=bool(row["has_zoom"]),
                has_micro=bool(row["has_micro"]),
                has_dynamic=bool(row["has_dynamic"]),
                has_people_analytics=bool(row["has_people_analytics"]),
                has_cars_analytics=bool(row["has_cars_analytics"]),
                has_special_cars_analytics=bool(row["has_special_cars_analytics"]),
                picture=row["picture"] or "",
                description=row["description"] or "",
            ))
        return cameras

    except Exception as e:
        logger.error(f"DB error: {e}", exc_info=True)
        return []


def get_camera_by_id(camera_id: int) -> Optional[Camera]:
    """Получить камеру по ID"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM main_camera WHERE id = ?", (camera_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Camera(
            id=row["id"],
            name=row["name"],
            price=row["price"],
            resolution=row["resolution"],
            type=row["type"],
            night_vision_technology=row["night_vision_technology"],
            connection_type=row["connection_type"],
            lens=row["lens"],
            has_zoom=bool(row["has_zoom"]),
            has_micro=bool(row["has_micro"]),
            has_dynamic=bool(row["has_dynamic"]),
            has_people_analytics=bool(row["has_people_analytics"]),
            has_cars_analytics=bool(row["has_cars_analytics"]),
            has_special_cars_analytics=bool(row["has_special_cars_analytics"]),
            picture=row["picture"] or "",
            description=row["description"] or "",
        )

    except Exception as e:
        logger.error(f"DB error get_camera_by_id: {e}", exc_info=True)
        return None


def get_distinct_values(field: str) -> List[str]:
    """Получить уникальные значения поля для фильтров"""
    allowed_fields = {
        "type", "resolution", "night_vision_technology",
        "connection_type", "lens"
    }
    if field not in allowed_fields:
        return []
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT DISTINCT {field} FROM main_camera WHERE {field} != '' ORDER BY {field}")
        rows = cursor.fetchall()
        conn.close()
        return [str(row[0]) for row in rows if row[0] is not None]
    except Exception as e:
        logger.error(f"DB error get_distinct_values: {e}", exc_info=True)
        return []


def get_cable_price() -> int:
    """Получить цену кабеля за метр"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT price_per_meter FROM main_cablesettings WHERE is_active = 1 LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row["price_per_meter"] if row else 125
    except Exception as e:
        logger.error(f"DB error get_cable_price: {e}", exc_info=True)
        return 125