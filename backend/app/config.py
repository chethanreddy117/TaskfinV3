from pydantic_settings import BaseSettings
from pydantic import ConfigDict, model_validator
from dotenv import load_dotenv
import os

# Load .env file from app directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)


class Settings(BaseSettings):
    DATABASE_URL: str | None = None
    POSTGRES_URL: str | None = None
    
    # Individual database connection parameters for SQLAlchemy
    user: str | None = None
    password: str | None = None
    host: str | None = None
    port: str | None = None
    dbname: str | None = None
    
    JWT_SECRET_KEY: str
    ANTHROPIC_API_KEY: str
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"

    @model_validator(mode='after')
    def assemble_db_connection(self):
        # First, try using DATABASE_URL or POSTGRES_URL directly
        if not self.DATABASE_URL:
            if self.POSTGRES_URL:
                self.DATABASE_URL = self.POSTGRES_URL
            # Build from individual parameters
            elif self.user and self.password and self.host:
                port = self.port or "5432"
                dbname = self.dbname or "postgres"
                self.DATABASE_URL = f"postgresql://{self.user}:{self.password}@{self.host}:{port}/{dbname}"
        
        # Clean the connection URL
        if self.DATABASE_URL:
            # Convert postgres:// to postgresql://
            if self.DATABASE_URL.startswith("postgres://"):
                self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
            
            # Remove invalid Supabase parameters like &supa=base-pooler.x
            # These parameters are not valid PostgreSQL connection options
            if "&supa=" in self.DATABASE_URL:
                # Split by '?' to separate base URL from parameters
                if "?" in self.DATABASE_URL:
                    base_url, params = self.DATABASE_URL.split("?", 1)
                    # Remove the supa parameter
                    params = "&".join([p for p in params.split("&") if not p.startswith("supa=")])
                    # Reconstruct URL
                    if params:
                        self.DATABASE_URL = f"{base_url}?{params}"
                    else:
                        self.DATABASE_URL = base_url
        
        return self

    model_config = ConfigDict(
        extra="ignore"
    )

settings = Settings()
