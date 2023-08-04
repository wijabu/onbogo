from decouple import config

# base config class
class Config(object):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

    SECRET_KEY = config('SECRET_KEY')

    DATABASE_URI = config('DATABASE_URI')

    SENDER_EMAIL = config('SENDER_EMAIL')
    SENDER_PASSWORD = config('SENDER_PASSWORD')
    API_TOKEN = config('API_TOKEN')
    USER_KEY = config('USER_KEY')
    
    REGISTER_KEY = config('REGISTER_KEY')


class ProductionConfig(Config):
    ENV = "production"


class DevelopmentConfig(Config):
    ENV = "development"
    DEBUG = True

    SESSION_COOKIE_SECURE = False

    HOST = "127.0.0.1"
    PORT = 8080


class TestingConfig(Config):
    TESTING = True

    SESSION_COOKIE_SECURE = False