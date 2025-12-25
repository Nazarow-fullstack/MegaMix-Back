import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-for-dev")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- ВОТ ЭТОГО НЕ ХВАТАЛО ---
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Исправляет ссылку для SQLAlchemy (нужно для Render.com)
        """
        if not self.DATABASE_URL:
            # Если в .env пусто, возвращаем локальную базу (чтобы не падало)
            return "postgresql://postgres:password@localhost:5432/megamix"

        # Render выдает postgres://, а SQLAlchemy требует postgresql://
        if self.DATABASE_URL.startswith("postgres://"):
            return self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
        return self.DATABASE_URL

settings = Settings()