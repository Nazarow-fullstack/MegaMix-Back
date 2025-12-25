import typer
import uvicorn
import os
from db_config import get_db
cli = typer.Typer()

@cli.command()
def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    get_db()
    uvicorn.run("main:app", host=host, port=port, reload=reload)

@cli.command()
def db_migrate(message: str):
    typer.echo(f"Создание миграции: {message}")
    os.system(f'alembic revision --autogenerate -m "{message}"')

@cli.command()
def db_upgrade(revision: str = "head"):
    typer.echo(f"Применение миграций до ревизии: {revision}")
    os.system(f"alembic upgrade {revision}")

if __name__ == "__main__":
    cli()