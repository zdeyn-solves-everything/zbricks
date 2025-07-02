import os

class Settings:
    MODE = os.getenv("APP_MODE", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    def validate(self):
        if self.MODE == "production" and self.SECRET_KEY == "dev-secret":
            raise RuntimeError("SECURITY ERROR: You must set SECRET_KEY in production!")

settings = Settings()
settings.validate()
