from .models import ORMBase

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import config

class Database:
    def __init__(self):
        self.engine = None
        self._connected = False
        self._init_engine()

    def _init_engine(self):
        if not self.engine:
            database_url = (
                f"mysql+pymysql://{config.DATABASE_USERNAME}:"
                f"{config.DATABASE_PASSWORD}@"
                f"{config.DATABASE_HOST}:"
                f"{config.DATABASE_PORT}/"
                f"{config.DATABASE_NAME}"
            )

            self.engine = create_engine(database_url)
            ORMBase.metadata.create_all(self.engine)
            try:
                with self.engine.connect(): ...
            except OperationalError as e:
                raise RuntimeError("Unable to connect to database") from e

    def disconnect(self):
        if self.engine:
            self.engine.dispose()
            self.engine = None

Database()