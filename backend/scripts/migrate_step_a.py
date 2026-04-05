"""
Migration: Step A — adds new columns and app_settings table.
Safe to run multiple times (uses IF NOT EXISTS / ADD COLUMN IF NOT EXISTS).

Run: .venv\Scripts\python scripts\migrate_step_a.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from app.database import engine
import app.models  # noqa — registers all models with Base


DEFAULT_SETTINGS = [
    ("bot_welcome_text",
     "👋 Привет! Добро пожаловать в VPN сервис.\n\nНажми кнопку ниже чтобы перейти в приложение.",
     "Текст приветственного сообщения бота"),
    ("bot_welcome_image_url", "", "URL картинки в приветственном сообщении (оставь пустым чтобы без картинки)"),
    ("bot_welcome_button_text", "🚀 Открыть приложение", "Текст кнопки открытия Mini App"),
    ("trial_description", "Попробуй бесплатно 3 дня без ограничений!", "Текст описания триала"),
    ("referral_percent_per_day", "5",
     "Процент от стоимости одного дня подписки реферала, начисляемый рефереру (в %)"),
]


async def _column_exists(conn, table: str, column: str) -> bool:
    r = await conn.execute(text(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"
    ), {"t": table, "c": column})
    return r.scalar() > 0


async def _index_exists(conn, table: str, index: str) -> bool:
    r = await conn.execute(text(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND INDEX_NAME = :i"
    ), {"t": table, "i": index})
    return r.scalar() > 0


async def run():
    async with engine.begin() as conn:
        print("▶ Добавляю колонку login_token в users...")
        if not await _column_exists(conn, "users", "login_token"):
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN login_token VARCHAR(64) NULL UNIQUE"
            ))
            print("  → добавлена")
        else:
            print("  → уже существует, пропускаю")

        print("▶ Добавляю индекс ix_users_login_token...")
        if not await _index_exists(conn, "users", "ix_users_login_token"):
            await conn.execute(text(
                "CREATE INDEX ix_users_login_token ON users (login_token)"
            ))
            print("  → добавлен")
        else:
            print("  → уже существует, пропускаю")

        print("▶ Добавляю колонку price_stars в plans...")
        if not await _column_exists(conn, "plans", "price_stars"):
            await conn.execute(text(
                "ALTER TABLE plans ADD COLUMN price_stars INT NULL"
            ))
            print("  → добавлена")
        else:
            print("  → уже существует, пропускаю")

        print("▶ Создаю таблицу app_settings...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS app_settings (
                `key` VARCHAR(128) NOT NULL PRIMARY KEY,
                `value` TEXT NULL,
                `description` VARCHAR(512) NULL,
                `is_public` BOOLEAN NOT NULL DEFAULT TRUE,
                `updated_at` DATETIME NOT NULL DEFAULT NOW() ON UPDATE NOW()
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """))

        print("▶ Заполняю дефолтные настройки (пропускаю существующие)...")
        for key, value, description in DEFAULT_SETTINGS:
            await conn.execute(text(
                "INSERT IGNORE INTO app_settings (`key`, `value`, `description`) "
                "VALUES (:key, :value, :desc)"
            ), {"key": key, "value": value, "desc": description})

        print("✅ Миграция завершена!")


if __name__ == "__main__":
    asyncio.run(run())
