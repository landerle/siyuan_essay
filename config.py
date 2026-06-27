import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
COMPOSITION_DIR = os.path.join(DATA_DIR, "compositions")
EXPORT_DIR = os.path.join(DATA_DIR, "exports")
DATABASE_PATH = os.path.join(DATA_DIR, "database.db")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")

SUPPORTED_EXTENSIONS = [".txt", ".docx"]

DEFAULT_CATEGORY = "其他"

def ensure_directories():
    for dir_path in [DATA_DIR, COMPOSITION_DIR, EXPORT_DIR, PROMPTS_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
