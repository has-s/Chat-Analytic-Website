from flask import Flask
from config import Config
from celery import Celery

celery = Celery(__name__, broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from routes import main
    app.register_blueprint(main)

    celery.conf.update(app.config)
    return app