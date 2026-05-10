# bot/sheets_sync.py
"""
Синхронизация данных из Google Sheets → Django SQLite DB.

Структура листа "Камеры" (строка 1 — заголовок, строки 2+ — данные):
| A  | B    | C            | D     | E           | F          | G    | H                       | I               | J    | K         | L           | M        | N                    | O                  | P                          |
| id | name | is_available | price | description | resolution | type | night_vision_technology | connection_type | lens | has_micro | has_dynamic | has_zoom | has_people_analytics | has_cars_analytics | has_special_cars_analytics |
"""
import logging
import sqlite3

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from . import config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
CAMERAS_SHEET = "Камеры"
CAMERAS_RANGE = f"{CAMERAS_SHEET}!A2:P"  # A..P — 16 колонок


class GoogleSheetsSync:
    """Читает данные из Google Sheets."""

    def __init__(self, spreadsheet_id: str, credentials_file: str):
        self.spreadsheet_id = spreadsheet_id
        self.credentials_file = credentials_file
        self._service = None

    def _get_service(self):
        if self._service is None:
            creds = Credentials.from_service_account_file(
                self.credentials_file, scopes=SCOPES
            )
            self._service = build("sheets", "v4", credentials=creds)
        return self._service

    @staticmethod
    def _parse_bool(value: str) -> bool:
        return str(value).strip().upper() in ("TRUE", "ДА", "YES", "1", "+")

    @staticmethod
    def _get(row: list, idx: int, default="") -> str:
        """Безопасно получает значение из строки по индексу."""
        return str(row[idx]).strip() if len(row) > idx and row[idx] else default

    def read_cameras(self) -> list[dict]:
        try:
            service = self._get_service()
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=CAMERAS_RANGE)
                .execute()
            )

            rows = result.get("values", [])
            logger.info(f"Прочитано {len(rows)} строк из листа '{CAMERAS_SHEET}'")

            cameras = []
            for i, row in enumerate(rows, start=2):
                if not row or not row[0]:
                    continue
                try:
                    cameras.append({
                        "id":                        int(row[0]),
                        "name":                      self._get(row, 1),
                        "is_available":              self._parse_bool(self._get(row, 2, "TRUE")),
                        "price":                     int(self._get(row, 3, "0")),
                        "description":               self._get(row, 4),
                        "resolution":                int(self._get(row, 5, "2")),
                        "type":                      self._get(row, 6, "Купольная"),
                        "night_vision_technology":   self._get(row, 7, "Color"),
                        "connection_type":           self._get(row, 8, "Провод"),
                        "lens":                      self._get(row, 9),
                        "has_micro":                 self._parse_bool(self._get(row, 10)),
                        "has_dynamic":               self._parse_bool(self._get(row, 11)),
                        "has_zoom":                  self._parse_bool(self._get(row, 12)),
                        "has_people_analytics":      self._parse_bool(self._get(row, 13)),
                        "has_cars_analytics":        self._parse_bool(self._get(row, 14)),
                        "has_special_cars_analytics":self._parse_bool(self._get(row, 15)),
                    })
                except (ValueError, IndexError) as e:
                    logger.warning(f"Строка {i}: ошибка парсинга — {e}, данные: {row}")

            return cameras

        except Exception as e:
            logger.error(f"Ошибка чтения Google Sheets: {e}")
            raise


class DBSync:
    """Применяет данные из Google Sheets в SQLite базу Django."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def sync_cameras(self, cameras: list[dict]) -> dict:
        """Обновляет существующие камеры или создаёт новые по id."""
        stats = {"updated": 0, "created": 0, "errors": 0}

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for camera in cameras:
                try:
                    cursor.execute("SELECT id FROM main_camera WHERE id = ?", (camera["id"],))
                    exists = cursor.fetchone()

                    if exists:
                        cursor.execute("""
                            UPDATE main_camera SET
                                name                      = ?,
                                is_available              = ?,
                                price                     = ?,
                                description               = ?,
                                resolution                = ?,
                                type                      = ?,
                                night_vision_technology   = ?,
                                connection_type           = ?,
                                lens                      = ?,
                                has_micro                 = ?,
                                has_dynamic               = ?,
                                has_zoom                  = ?,
                                has_people_analytics      = ?,
                                has_cars_analytics        = ?,
                                has_special_cars_analytics= ?
                            WHERE id = ?
                        """, (
                            camera["name"],
                            1 if camera["is_available"] else 0,
                            camera["price"],
                            camera["description"],
                            camera["resolution"],
                            camera["type"],
                            camera["night_vision_technology"],
                            camera["connection_type"],
                            camera["lens"],
                            1 if camera["has_micro"] else 0,
                            1 if camera["has_dynamic"] else 0,
                            1 if camera["has_zoom"] else 0,
                            1 if camera["has_people_analytics"] else 0,
                            1 if camera["has_cars_analytics"] else 0,
                            1 if camera["has_special_cars_analytics"] else 0,
                            camera["id"],
                        ))
                        stats["updated"] += 1
                        logger.debug(f"Обновлена камера id={camera['id']}: {camera['name']}")

                    else:
                        cursor.execute("""
                            INSERT INTO main_camera (
                                id, name, is_available, price, description,
                                resolution, type, night_vision_technology,
                                connection_type, lens,
                                has_micro, has_dynamic, has_zoom,
                                has_people_analytics, has_cars_analytics,
                                has_special_cars_analytics
                            ) VALUES (
                                ?, ?, ?, ?, ?,
                                ?, ?, ?,
                                ?, ?,
                                ?, ?, ?,
                                ?, ?, ?
                            )
                        """, (
                            camera["id"],
                            camera["name"],
                            1 if camera["is_available"] else 0,
                            camera["price"],
                            camera["description"],
                            camera["resolution"],
                            camera["type"],
                            camera["night_vision_technology"],
                            camera["connection_type"],
                            camera["lens"],
                            1 if camera["has_micro"] else 0,
                            1 if camera["has_dynamic"] else 0,
                            1 if camera["has_zoom"] else 0,
                            1 if camera["has_people_analytics"] else 0,
                            1 if camera["has_cars_analytics"] else 0,
                            1 if camera["has_special_cars_analytics"] else 0,
                        ))
                        stats["created"] += 1
                        logger.debug(f"Создана камера id={camera['id']}: {camera['name']}")

                except sqlite3.Error as e:
                    logger.error(f"Ошибка при обработке камеры id={camera['id']}: {e}")
                    stats["errors"] += 1
                    continue

            conn.commit()
            logger.info(f"Синхронизация завершена: {stats}")

        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise
        finally:
            conn.close()

        return stats


class SheetsManager:
    """Фасад — объединяет GoogleSheetsSync и DBSync."""

    def __init__(self):
        self.sheets = GoogleSheetsSync(
            spreadsheet_id=config.SPREADSHEET_ID,
            credentials_file=config.GOOGLE_CREDENTIALS_FILE,
        )
        self.db = DBSync(config.DJANGO_DB_PATH)

    def sync_all(self) -> dict:
        cameras = self.sheets.read_cameras()
        return self.db.sync_cameras(cameras)