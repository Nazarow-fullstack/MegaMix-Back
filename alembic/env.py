from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# --- 1. Добавляем путь к корню проекта ---
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# --- 2. ИМПОРТЫ ПОД ТВОЮ СТРУКТУРУ ---
from core.config import settings

# ВАЖНО: У тебя файл называется db_config.py и лежит в корне, берем Base оттуда
from db_config import Base 

# Импортируем модули (папка modules лежит в корне)
from modules.auth import models as auth_models
from modules.inventory import models as inventory_models
from modules.clients import models as client_models
from modules.sales import models as sales_models
from modules.expenses import models as expense_models 

config = context.config

# --- 3. Подставляем URL из настроек ---
section = config.config_ini_section
config.set_section_option(section, "sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()