import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./audit_demo.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "demo-secret-key-not-for-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    AUDIT_PERIOD_START: str = "2025-01-01"
    AUDIT_PERIOD_END: str = "2025-12-31"
    MATERIALITY_TOLERANCE: float = 0.01  # 1 cent absolute tolerance for exact matches
    CONFIDENCE_REVIEW_THRESHOLD: float = 0.85

settings = Settings()
