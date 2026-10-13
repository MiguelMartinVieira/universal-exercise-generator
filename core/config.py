import os
from dotenv import load_dotenv

# Load .env from project root or parent directories
load_dotenv()


class Config:
    @property
    def api_key(self):
        return os.environ.get("API_KEY")

    @property
    def paid_api_key(self):
        return os.environ.get("PAID_API_KEY")

    @property
    def best_api_key(self):
        return self.paid_api_key or self.api_key

    @property
    def project_root(self):
        # Universal_Generator/core/config.py -> Universal_Generator
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    class Models:
        # Modelos vigentes (los antiguos gemini-3-*-preview fueron retirados -> 404)
        STANDARD = "gemini-3.5-flash"
        PRO = "gemini-pro-latest"


# Singleton instance
global_config = Config()
