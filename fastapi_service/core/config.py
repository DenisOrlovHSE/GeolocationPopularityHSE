from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///atm_predictions.db"
    model_path: str = "models/best_linear_model.pkl"
    training_data_path: str = "dataset/atm_train_split.csv"
    
    class Config:
        env_file = ".env"
        extra = 'ignore'


settings = Settings()