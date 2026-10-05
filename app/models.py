from sqlalchemy import Column, Integer, String, Date, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)

    auth_user_id = Column(
        Integer,
        ForeignKey("auth_users.auth_user_id"),
        unique=True,
        nullable=False
    )

    name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String, nullable=False)
    contact = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    auth_user = relationship(
        "AuthUser",
        back_populates="user"
    )

    vaccination_records = relationship(
        "VaccinationRecord",
        back_populates="user"
    )

    predictions = relationship(
        "Prediction",
        back_populates="user"
    )


class Vaccine(Base):
    __tablename__ = "vaccines"

    vaccine_id = Column(Integer, primary_key=True, index=True)
    vaccine_name = Column(String, nullable=False)
    description = Column(String)

    vaccination_records = relationship(
        "VaccinationRecord",
        back_populates="vaccine"
    )


class VaccinationRecord(Base):
    __tablename__ = "vaccination_records"

    record_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.user_id"),
        nullable=False
    )

    vaccine_id = Column(
        Integer,
        ForeignKey("vaccines.vaccine_id"),
        nullable=False
    )

    dose_number = Column(Integer, nullable=False)
    vaccination_date = Column(Date, nullable=False)
    next_due_date = Column(Date)
    status = Column(String, nullable=False)

    user = relationship(
        "User",
        back_populates="vaccination_records"
    )

    vaccine = relationship(
        "Vaccine",
        back_populates="vaccination_records"
    )


class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id"),
        nullable=False
    )

    missed_probability = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)

    prediction_date = Column(
        DateTime,
        default=datetime.utcnow
    )

    user = relationship(
        "User",
        back_populates="predictions"
    )


class AuthUser(Base):
    __tablename__ = "auth_users"

    auth_user_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        unique=True,
        nullable=False
    )

    password_hash = Column(
        String,
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="auth_user",
        uselist=False
    )