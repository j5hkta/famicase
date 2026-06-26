import os
from dotenv import load_dotenv

load_dotenv()

# En Railway los datos van al volumen persistente en /data; en local van a instance/
_ON_RAILWAY = bool(os.environ.get('RAILWAY_ENVIRONMENT'))
DATA_DIR = '/data' if _ON_RAILWAY else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(DATA_DIR, 'dental.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATA_DIR = DATA_DIR
    LAB_NOMBRE = os.environ.get('LAB_NOMBRE', 'FamiCase')
    LAB_PROPIETARIOS = os.environ.get('LAB_PROPIETARIOS', 'Oscar Huánuco & Santa Loayza')
    LAB_TELEFONO_SANTA = os.environ.get('LAB_TELEFONO_SANTA', '990 469 653')
    LAB_TELEFONO_OSCAR = os.environ.get('LAB_TELEFONO_OSCAR', '988 880 196')
    LAB_CIUDAD = os.environ.get('LAB_CIUDAD', 'Lima, Perú')
