from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://examshield:examshield@db:5432/examshield"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    evidence_dir: str = "/srv/evidence"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    admin_email: str = "admin@example.com"
    admin_password: str = "change-me-now"

    class Config:
        env_file = ".env"


settings = Settings()
