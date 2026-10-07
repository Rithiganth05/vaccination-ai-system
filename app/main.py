from datetime import date

import joblib
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import (
    AuthUser,
    Base,
    Prediction,
    User,
    VaccinationRecord,
    Vaccine,
)
from app.schemas import (
    PredictionCreate,
    PredictionResponse,
    RegisterRequest,
    UserResponse,
    VaccinationRecordCreate,
    VaccinationRecordResponse,
    VaccinationRecordUpdate,
    VaccineCreate,
    VaccineResponse,
    VaccineUpdate,
)
from app.security import (
    create_access_token,
    hash_password,
    verify_access_token,
    verify_password,
)

Base.metadata.create_all(bind=engine)
model = joblib.load("ml/vaccination_model.pkl")

app = FastAPI(
    title="Vaccination Tracking API",
    description="AI-Based Vaccination Tracking and Prediction System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    username = verify_access_token(token)

    if not username:
        raise HTTPException(401, "Invalid or expired token")

    user = db.query(AuthUser).filter(
        AuthUser.username == username
    ).first()

    if not user:
        raise HTTPException(401, "User not found")

    return user


def get_logged_in_profile(current_user, db: Session):
    user = db.query(User).filter(
        User.auth_user_id == current_user.auth_user_id
    ).first()

    if not user:
        raise HTTPException(404, "User profile not found")

    return user


@app.get("/")
def root():
    return {"message": "Vaccination Tracking API is running"}


@app.get("/db-test")
def database_test(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"message": "FastAPI is connected to PostgreSQL"}
    except Exception:
        raise HTTPException(500, "Database connection failed")


@app.get("/users/me", response_model=UserResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_logged_in_profile(current_user, db)


@app.post("/vaccines", response_model=VaccineResponse)
def create_vaccine(
    vaccine: VaccineCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if db.query(Vaccine).filter(
        Vaccine.vaccine_name == vaccine.vaccine_name
    ).first():
        raise HTTPException(400, "Vaccine already exists")

    new_vaccine = Vaccine(
        vaccine_name=vaccine.vaccine_name,
        description=vaccine.description,
    )

    db.add(new_vaccine)
    db.commit()
    db.refresh(new_vaccine)

    return new_vaccine


@app.get("/vaccines", response_model=list[VaccineResponse])
def get_vaccines(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(Vaccine).order_by(
        Vaccine.vaccine_id.asc()
    ).all()


@app.get("/vaccines/{vaccine_id}", response_model=VaccineResponse)
def get_vaccine(
    vaccine_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    vaccine = db.query(Vaccine).filter(
        Vaccine.vaccine_id == vaccine_id
    ).first()

    if not vaccine:
        raise HTTPException(404, "Vaccine not found")

    return vaccine


@app.put("/vaccines/{vaccine_id}", response_model=VaccineResponse)
def update_vaccine(
    vaccine_id: int,
    vaccine_data: VaccineUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    vaccine = db.query(Vaccine).filter(
        Vaccine.vaccine_id == vaccine_id
    ).first()

    if not vaccine:
        raise HTTPException(404, "Vaccine not found")

    vaccine.vaccine_name = vaccine_data.vaccine_name
    vaccine.description = vaccine_data.description

    db.commit()
    db.refresh(vaccine)

    return vaccine


@app.delete("/vaccines/{vaccine_id}")
def delete_vaccine(
    vaccine_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    vaccine = db.query(Vaccine).filter(
        Vaccine.vaccine_id == vaccine_id
    ).first()

    if not vaccine:
        raise HTTPException(404, "Vaccine not found")

    if db.query(VaccinationRecord).filter(
        VaccinationRecord.vaccine_id == vaccine_id
    ).first():
        raise HTTPException(
            400,
            "Cannot delete vaccine because vaccination records use it",
        )

    db.delete(vaccine)
    db.commit()

    return {"message": "Vaccine deleted successfully"}


@app.post(
    "/vaccination-records",
    response_model=VaccinationRecordResponse,
)
def create_vaccination_record(
    record_data: VaccinationRecordCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = get_logged_in_profile(current_user, db)

    if record_data.user_id != user.user_id:
        raise HTTPException(
            403,
            "You can only create records for your own account",
        )

    vaccine = db.query(Vaccine).filter(
        Vaccine.vaccine_id == record_data.vaccine_id
    ).first()

    if not vaccine:
        raise HTTPException(404, "Vaccine not found")

    if record_data.dose_number < 1:
        raise HTTPException(400, "Dose number must be at least 1")

    if (
        record_data.next_due_date
        and record_data.next_due_date < record_data.vaccination_date
    ):
        raise HTTPException(
            400,
            "Next due date cannot be before vaccination date",
        )

    record = VaccinationRecord(
        user_id=user.user_id,
        vaccine_id=record_data.vaccine_id,
        dose_number=record_data.dose_number,
        vaccination_date=record_data.vaccination_date,
        next_due_date=record_data.next_due_date,
        status=record_data.status,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@app.get(
    "/vaccination-records",
    response_model=list[VaccinationRecordResponse],
)
def get_vaccination_records(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = get_logged_in_profile(current_user, db)

    return db.query(VaccinationRecord).filter(
        VaccinationRecord.user_id == user.user_id
    ).order_by(
        VaccinationRecord.vaccination_date.asc()
    ).all()


@app.get(
    "/vaccination-records/{record_id}",
    response_model=VaccinationRecordResponse,
)
def get_vaccination_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = get_logged_in_profile(current_user, db)

    record = db.query(VaccinationRecord).filter(
        VaccinationRecord.record_id == record_id,
        VaccinationRecord.user_id == user.user_id,
    ).first()

    if not record:
        raise HTTPException(404, "Vaccination record not found")

    return record


@app.put(
    "/vaccination-records/{record_id}",
    response_model=VaccinationRecordResponse,
)
def update_vaccination_record(
    record_id: int,
    record_data: VaccinationRecordUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = get_logged_in_profile(current_user, db)

    record = db.query(VaccinationRecord).filter(
        VaccinationRecord.record_id == record_id,
        VaccinationRecord.user_id == user.user_id,
    ).first()

    if not record:
        raise HTTPException(404, "Vaccination record not found")

    vaccine = db.query(Vaccine).filter(
        Vaccine.vaccine_id == record_data.vaccine_id
    ).first()

    if not vaccine:
        raise HTTPException(404, "Vaccine not found")

    if record_data.dose_number < 1:
        raise HTTPException(400, "Dose number must be at least 1")

    if (
        record_data.next_due_date
        and record_data.next_due_date < record_data.vaccination_date
    ):
        raise HTTPException(
            400,
            "Next due date cannot be before vaccination date",
        )

    record.vaccine_id = record_data.vaccine_id
    record.dose_number = record_data.dose_number
    record.vaccination_date = record_data.vaccination_date
    record.next_due_date = record_data.next_due_date
    record.status = record_data.status

    db.commit()
    db.refresh(record)

    return record


@app.delete("/vaccination-records/{record_id}")
def delete_vaccination_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = get_logged_in_profile(current_user, db)

    record = db.query(VaccinationRecord).filter(
        VaccinationRecord.record_id == record_id,
        VaccinationRecord.user_id == user.user_id,
    ).first()

    if not record:
        raise HTTPException(404, "Vaccination record not found")

    db.delete(record)
    db.commit()

    return {"message": "Vaccination record deleted successfully"}


@app.post("/predictions", response_model=PredictionResponse)
def create_prediction(
    prediction_data: PredictionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = get_logged_in_profile(current_user, db)

    if prediction_data.user_id != user.user_id:
        raise HTTPException(
            403,
            "You can only create predictions for your own account",
        )

    records = db.query(VaccinationRecord).filter(
        VaccinationRecord.user_id == user.user_id
    ).order_by(
        VaccinationRecord.vaccination_date.asc()
    ).all()

    if not records:
        raise HTTPException(
            400,
            "Add at least one vaccination record before generating a prediction",
        )

    today = date.today()
    age = today.year - user.date_of_birth.year

    if (today.month, today.day) < (
        user.date_of_birth.month,
        user.date_of_birth.day,
    ):
        age -= 1

    latest = records[-1]
    dose_number = latest.dose_number
    days_late = 0

    if latest.next_due_date:
        days_late = max(
            0,
            (today - latest.next_due_date).days,
        )

    previous_missed = sum(
        1
        for record in records
        if (record.status or "").lower() == "missed"
    )

    features = [[
        age,
        dose_number,
        days_late,
        previous_missed,
        len(records),
    ]]

    try:
        probability = model.predict_proba(features)[0][1]
    except Exception:
        raise HTTPException(500, "Unable to generate AI prediction")

    missed_probability = round(float(probability) * 100, 2)

    if missed_probability >= 70:
        risk_level = "High"
    elif missed_probability >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    prediction = Prediction(
        user_id=user.user_id,
        missed_probability=missed_probability,
        risk_level=risk_level,
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return prediction


@app.get("/predictions", response_model=list[PredictionResponse])
def get_predictions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = get_logged_in_profile(current_user, db)

    return db.query(Prediction).filter(
        Prediction.user_id == user.user_id
    ).order_by(
        Prediction.prediction_date.desc()
    ).all()


@app.get(
    "/predictions/{prediction_id}",
    response_model=PredictionResponse,
)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = get_logged_in_profile(current_user, db)

    prediction = db.query(Prediction).filter(
        Prediction.prediction_id == prediction_id,
        Prediction.user_id == user.user_id,
    ).first()

    if not prediction:
        raise HTTPException(404, "Prediction not found")

    return prediction


@app.get("/users/{user_id}/summary")
def get_user_summary(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = get_logged_in_profile(current_user, db)

    if user.user_id != user_id:
        raise HTTPException(
            403,
            "You are not allowed to access this user's summary",
        )

    records = db.query(VaccinationRecord).filter(
        VaccinationRecord.user_id == user.user_id
    ).order_by(
        VaccinationRecord.vaccination_date.asc()
    ).all()

    latest_prediction = db.query(Prediction).filter(
        Prediction.user_id == user.user_id
    ).order_by(
        Prediction.prediction_date.desc()
    ).first()

    history = [
        {
            "record_id": record.record_id,
            "vaccine_name": (
                record.vaccine.vaccine_name
                if record.vaccine else None
            ),
            "dose_number": record.dose_number,
            "vaccination_date": record.vaccination_date,
            "next_due_date": record.next_due_date,
            "status": record.status,
        }
        for record in records
    ]

    prediction = None

    if latest_prediction:
        prediction = {
            "prediction_id": latest_prediction.prediction_id,
            "missed_probability": latest_prediction.missed_probability,
            "risk_level": latest_prediction.risk_level,
            "prediction_date": latest_prediction.prediction_date,
        }

    return {
        "user": {
            "user_id": user.user_id,
            "name": user.name,
            "date_of_birth": user.date_of_birth,
            "gender": user.gender,
            "contact": user.contact,
        },
        "vaccination_history": history,
        "latest_prediction": prediction,
    }


@app.get(
    "/users/{user_id}/predictions",
    response_model=list[PredictionResponse],
)
def get_user_predictions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = get_logged_in_profile(current_user, db)

    if user.user_id != user_id:
        raise HTTPException(
            403,
            "You are not allowed to access these predictions",
        )

    return db.query(Prediction).filter(
        Prediction.user_id == user.user_id
    ).order_by(
        Prediction.prediction_date.desc()
    ).all()


@app.post("/auth/register")
def register_user(
    register_data: RegisterRequest,
    db: Session = Depends(get_db),
):
    if db.query(AuthUser).filter(
        AuthUser.username == register_data.username
    ).first():
        raise HTTPException(400, "Username already exists")

    username = register_data.username.strip()

    if len(username) < 3:
        raise HTTPException(
            400,
            "Username must contain at least 3 characters",
        )

    if len(register_data.password) < 6:
        raise HTTPException(
            400,
            "Password must contain at least 6 characters",
        )

    auth_user = AuthUser(
        username=username,
        password_hash=hash_password(register_data.password),
    )

    try:
        db.add(auth_user)
        db.flush()

        user = User(
            auth_user_id=auth_user.auth_user_id,
            name=register_data.name,
            date_of_birth=register_data.date_of_birth,
            gender=register_data.gender,
            contact=register_data.contact,
        )

        db.add(user)
        db.commit()
        db.refresh(auth_user)
        db.refresh(user)

        return {
            "message": "User registered successfully",
            "auth_user_id": auth_user.auth_user_id,
            "user_id": user.user_id,
            "username": auth_user.username,
        }

    except Exception:
        db.rollback()
        raise HTTPException(500, "Unable to register user")


@app.post("/auth/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    auth_user = db.query(AuthUser).filter(
        AuthUser.username == form_data.username
    ).first()

    if not auth_user or not verify_password(
        form_data.password,
        auth_user.password_hash,
    ):
        raise HTTPException(401, "Invalid username or password")

    user = db.query(User).filter(
        User.auth_user_id == auth_user.auth_user_id
    ).first()

    if not user:
        raise HTTPException(404, "User profile not found")

    token = create_access_token({
        "sub": auth_user.username,
        "user_id": user.user_id,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "username": auth_user.username,
    }


@app.get("/auth/me")
def get_current_user_info(
    current_user=Depends(get_current_user),
):
    return {
        "auth_user_id": current_user.auth_user_id,
        "username": current_user.username,
    }


@app.get("/users/{user_id}/reminders")
def get_user_reminders(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = get_logged_in_profile(current_user, db)

    if user.user_id != user_id:
        raise HTTPException(
            403,
            "You are not allowed to access these reminders",
        )

    today = date.today()

    records = db.query(VaccinationRecord).filter(
        VaccinationRecord.user_id == user.user_id
    ).order_by(
        VaccinationRecord.next_due_date.asc()
    ).all()

    reminders = []

    for record in records:
        if not record.next_due_date:
            continue

        if record.next_due_date < today:
            status = "Overdue"
        elif record.next_due_date == today:
            status = "Due Today"
        else:
            status = "Upcoming"

        reminders.append({
            "record_id": record.record_id,
            "vaccine_name": (
                record.vaccine.vaccine_name
                if record.vaccine else None
            ),
            "dose_number": record.dose_number,
            "next_due_date": record.next_due_date,
            "status": status,
        })

    return {
        "user_id": user.user_id,
        "user_name": user.name,
        "reminders": reminders,
    }


@app.get("/dashboard/{user_id}")
def get_dashboard(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = get_logged_in_profile(current_user, db)

    if user.user_id != user_id:
        raise HTTPException(
            403,
            "You are not allowed to access this dashboard",
        )

    records = db.query(VaccinationRecord).filter(
        VaccinationRecord.user_id == user.user_id
    ).order_by(
        VaccinationRecord.vaccination_date.asc()
    ).all()

    latest_prediction = db.query(Prediction).filter(
        Prediction.user_id == user.user_id
    ).order_by(
        Prediction.prediction_date.desc()
    ).first()

    today = date.today()

    completed = sum(
        1 for r in records
        if (r.status or "").lower() == "completed"
    )

    missed = sum(
        1 for r in records
        if (r.status or "").lower() == "missed"
    )

    upcoming = 0
    overdue = 0
    reminders = []

    for record in records:
        if not record.next_due_date:
            continue

        if record.next_due_date < today:
            overdue += 1
            status = "Overdue"
        elif record.next_due_date == today:
            status = "Due Today"
        else:
            upcoming += 1
            status = "Upcoming"

        reminders.append({
            "record_id": record.record_id,
            "vaccine_name": (
                record.vaccine.vaccine_name
                if record.vaccine else None
            ),
            "dose_number": record.dose_number,
            "next_due_date": record.next_due_date,
            "status": status,
        })

    prediction = None

    if latest_prediction:
        prediction = {
            "prediction_id": latest_prediction.prediction_id,
            "missed_probability": latest_prediction.missed_probability,
            "risk_level": latest_prediction.risk_level,
            "prediction_date": latest_prediction.prediction_date,
        }

    return {
        "user": {
            "user_id": user.user_id,
            "name": user.name,
            "date_of_birth": user.date_of_birth,
            "gender": user.gender,
            "contact": user.contact,
        },
        "vaccination_summary": {
            "total_records": len(records),
            "completed": completed,
            "missed": missed,
            "upcoming": upcoming,
            "overdue": overdue,
        },
        "latest_prediction": prediction,
        "reminders": reminders,
    }