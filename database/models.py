from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

class ORMBase(DeclarativeBase): ...


class AmazonLogin(ORMBase):
    __tablename__ = 'amazon_login'

    email: Mapped[str] = mapped_column(String(100), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    access_token: Mapped[str] = mapped_column(Text)


class Login(ORMBase):
    __tablename__ = 'login'

    email: Mapped[str] = mapped_column(String(64), primary_key=True)
    password: Mapped[str] = mapped_column(Text)
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str] = mapped_column(Text)
    suscription: Mapped[bool] = mapped_column(Boolean)
    device_id: Mapped[str] = mapped_column(String(255))
