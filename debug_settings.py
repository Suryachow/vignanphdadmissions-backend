import sys
import os
sys.path.append(os.getcwd())
from app.core.config import settings
print("URL:", settings.DATABASE_URL)
