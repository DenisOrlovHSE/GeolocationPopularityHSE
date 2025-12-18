import os
from dotenv import load_dotenv


load_dotenv(override=True)


YANDEX_MAPS_API_KEY = os.getenv("YANDEX_MAPS_API_KEY")