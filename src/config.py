import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_path: str = "models/bestmodel.pkl"
    scaler_path: str = "models/preprocessor.pkl"
    alert_threshold: float = 0.8
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
