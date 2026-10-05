from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token
)

import joblib
from datetime import date

from app.database import engine, get_db

from app.models import (
    Base,
    User,
    Vaccine,
    VaccinationRecord,
    Prediction,
    AuthUser
)

from app.schemas import (
    UserResponse,
    VaccineCreate,
    VaccineUpdate,
    VaccineResponse,
    VaccinationRecordCreate,
    VaccinationRecordUpdate,
    VaccinationRecordResponse,
    PredictionCreate,
    PredictionResponse,
    RegisterRequest
)


# ==================================================
# DATABASE
# ==================================================

Base.metadata.create_all(bind=engine)


# ==================================================
# ML MODEL
# ==================================================

model = joblib.load("ml/vaccination_model.pkl")


# ==================================================
# FASTAPI APP
# ==================================================

app = FastAPI(
    title="Vaccination Tracking API",
    description="AI-Based Vaccination Tracking and Prediction System",
    version="1.0.0"
)


# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# AUTHENTICATION
# ==================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    username = verify_access_token(token)

    if username is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    auth_user = db.query(AuthUser).filter(
        AuthUser.username == username
    ).first()

    if not auth_user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return auth_user


def get_logged_in_profile(
    current_user: AuthUser,
    db: Session
):
    user = db.query(User).filter(
        User.auth_user_id == current_user.auth_user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )

    return user


# ==================================================
# ROOT
# ==================================================

@app.get("/")
def root():
    return {
        "message": "Vaccination Tracking API is running"
    }


# ==================================================
# DATABASE TEST
# ==================================================

@app.get("/db-test")
def database_test(
    db: Session = Depends(get_db)
):
    try:
        db.execute("SELECT 1")

        return {
            "message": "FastAPI is connected to PostgreSQL"
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )


# ==================================================
# USER PROFILE
# ==================================================

@app.get(
    "/users/me",
    response_model=UserResponse
)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    user = get_logged_in_profile(
        current_user,
        db
    )

    return user


# ==================================================
# VACCINES
# ==================================================

@app.post(
    "/vaccines",
    response_model=VaccineResponse
)
def create_vaccine(
    vaccine: VaccineCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    existing_vaccine = db.query(Vaccine).filter(
        Vaccine.vaccine_name == vaccine.vaccine_name
    ).first()

    if existing_vaccine:
        raise HTTPException(
            status_code=400,
            detail="Vaccine already exists"
        )

    new_vaccine = Vaccine(
        vaccine_name=vaccine.vaccine_name,
        description=vaccine.description
    )

    db.add(new_vaccine)
    db.commit()
    db.refresh(new_vaccine)

    return new_vaccine


@app.get(
    "/vaccines",
    response_model=list[VaccineResponse]
)
def get_vaccines(
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    vaccines = db.query(Vaccine).order_by(
        Vaccine.vaccine_id.asc()
    ).all()

    return vaccines


@app.get(
    "/vaccines/{vaccine_id}",
    response_model=VaccineResponse
)
def get_vaccine(
    vaccine_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    vaccine = db.query(Vaccine).filter(
        Vaccine.vaccine_id == vaccine_id
    ).first()

    if not vaccine:
        raise HTTPException(
            status_code=404,
            detail="Vaccine not found"
        )

    return vaccine


@app.put(
    "/vaccines/{vaccine_id}",
    response_model=VaccineResponse
)
def update_vaccine(
    vaccine_id: int,
    vaccine_data: VaccineUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    vaccine = db.query(Vaccine).filter(
        Vaccine.vaccine_id == vaccine_id
    ).first()

    if not vaccine:
        raise HTTPException(
            status_code=404,
            detail="Vaccine not found"
        )

    vaccine.vaccine_name = vaccine_data.vaccine_name
    vaccine.description = vaccine_data.description

    db.commit()
    db.refresh(vaccine)

    return vaccine


@app.delete("/vaccines/{vaccine_id}")
def delete_vaccine(
    vaccine_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    vaccine = db.query(Vaccine).filter(
        Vaccine.vaccine_id == vaccine_id
    ).first()

    if not vaccine:
        raise HTTPException(
            status_code=404,
            detail="Vaccine not found"
        )

    # Prevent deletion if vaccination records use this vaccine
    existing_record = db.query(
        VaccinationRecord
    ).filter(
        VaccinationRecord.vaccine_id == vaccine_id
    ).first()

    if existing_record:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete vaccine because vaccination records use it"
        )

    db.delete(vaccine)
    db.commit()

    return {
        "message": "Vaccine deleted successfully"
    }


# ==================================================
# VACCINATION RECORDS
# ==================================================

@app.post(
    "/vaccination-records",
    response_model=VaccinationRecordResponse
)
def create_vaccination_record(
    record_data: VaccinationRecordCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    user = get_logged_in_profile(
        current_user,
        db
    )

    # User can only create records for themselves
    if record_data.user_id != user.user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only create records for your own account"
        )

    # Check vaccine
    vaccine = db.query(Vaccine).filter(
        Vaccine.vaccine_id == record_data.vaccine_id
    ).first()

    if not vaccine:
        raise HTTPException(
            status_code=404,
            detail="Vaccine not found"
        )

    # Validate dose
    if record_data.dose_number < 1:
        raise HTTPException(
            status_code=400,
            detail="Dose number must be at least 1"
        )

    # Validate dates
    if (
        record_data.next_due_date
        and record_data.next_due_date < record_data.vaccination_date
    ):
        raise HTTPException(
            status_code=400,
            detail="Next due date cannot be before vaccination date"
        )

    record = VaccinationRecord(
        user_id=user.user_id,
        vaccine_id=record_data.vaccine_id,
        dose_number=record_data.dose_number,
        vaccination_date=record_data.vaccination_date,
        next_due_date=record_data.next_due_date,
        status=record_data.status
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@app.get(
    "/vaccination-records",
    response_model=list[VaccinationRecordResponse]
)
def get_vaccination_records(
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    user = get_logged_in_profile(
        current_user,
        db
    )

    records = db.query(
        VaccinationRecord
    ).filter(
        VaccinationRecord.user_id == user.user_id
    ).order_by(
        VaccinationRecord.vaccination_date.asc()
    ).all()

    return records


@app.get(
    "/vaccination-records/{record_id}",
    response_model=VaccinationRecordResponse
)
def get_vaccination_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    user = get_logged_in_profile(
        current_user,
        db
    )

    record = db.query(
        VaccinationRecord
    ).filter(
        VaccinationRecord.record_id == record_id,
        VaccinationRecord.user_id == user.user_id
    ).first()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Vaccination record not found"
        )

    return record


@app.put(
    "/vaccination-records/{record_id}",
    response_model=VaccinationRecordResponse
)
def update_vaccination_record(
    record_id: int,
    record_data: VaccinationRecordUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    user = get_logged_in_profile(
        current_user,
        db
    )

    # Find record belonging to logged-in user
    record = db.query(
        VaccinationRecord
    ).filter(
        VaccinationRecord.record_id == record_id,
        VaccinationRecord.user_id == user.user_id
    ).first()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Vaccination record not found"
        )

    # Check vaccine
    vaccine = db.query(Vaccine).filter(
        Vaccine.vaccine_id == record_data.vaccine_id
    ).first()

    if not vaccine:
        raise HTTPException(
            status_code=404,
            detail="Vaccine not found"
        )

    # Validate dose
    if record_data.dose_number < 1:
        raise HTTPException(
            status_code=400,
            detail="Dose number must be at least 1"
        )

    # Validate dates
    if (
        record_data.next_due_date
        and record_data.next_due_date < record_data.vaccination_date
    ):
        raise HTTPException(
            status_code=400,
            detail="Next due date cannot be before vaccination date"
        )

    # Keep ownership with logged-in user
    record.user_id = user.user_id
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
    current_user: AuthUser = Depends(get_current_user)
):
    user = get_logged_in_profile(
        current_user,
        db
    )

    record = db.query(
        VaccinationRecord
    ).filter(
        VaccinationRecord.record_id == record_id,
        VaccinationRecord.user_id == user.user_id
    ).first()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Vaccination record not found"
        )

    db.delete(record)
    db.commit()

    return {
        "message": "Vaccination record deleted successfully"
    }


# ==================================================
# AI PREDICTION
# ==================================================

@app.post(
    "/predictions",
    response_model=PredictionResponse
)
def create_prediction(
    prediction_data: PredictionCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    user = get_logged_in_profile(
        current_user,
        db
    )

    # User can only create prediction for themselves
    if prediction_data.user_id != user.user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only create predictions for your own account"
        )

    print("====================================")
    print("Prediction endpoint reached")
    print("Logged-in User ID:", user.user_id)
    print("====================================")

    # Get user's vaccination records
    records = db.query(
        VaccinationRecord
    ).filter(
        VaccinationRecord.user_id == user.user_id
    ).order_by(
        VaccinationRecord.vaccination_date.asc()
    ).all()

    # Require at least one record
    if not records:
        raise HTTPException(
            status_code=400,
            detail="Add at least one vaccination record before generating a prediction"
        )

    today = date.today()

    # ==================================================
    # CALCULATE AGE
    # ==================================================

    age = today.year - user.date_of_birth.year

    if (
        today.month,
        today.day
    ) < (
        user.date_of_birth.month,
        user.date_of_birth.day
    ):
        age -= 1

    # ==================================================
    # INITIAL FEATURES
    # ==================================================

    dose_number = 1
    days_late = 0
    previous_missed = 0
    total_doses = len(records)

    # ==================================================
    # LATEST RECORD
    # ==================================================

    latest_record = records[-1]

    dose_number = latest_record.dose_number

    if latest_record.next_due_date:
        days_late = max(
            0,
            (
                today -
                latest_record.next_due_date
            ).days
        )

    previous_missed = sum(
        1
        for record in records
        if (record.status or "").lower() == "missed"
    )

    # ==================================================
    # ML FEATURES
    # ==================================================

    features = [[
        age,
        dose_number,
        days_late,
        previous_missed,
        total_doses
    ]]

    print("ML Features:", features)

    # ==================================================
    # MODEL PREDICTION
    # ==================================================

    try:
        probability = model.predict_proba(
            features
        )[0][1]

    except Exception as error:
        print("ML prediction error:", error)

        raise HTTPException(
            status_code=500,
            detail="Unable to generate AI prediction"
        )

    missed_probability = round(
        float(probability) * 100,
        2
    )

    print(
        "Missed Probability:",
        missed_probability
    )

    # ==================================================
    # RISK LEVEL
    # ==================================================

    if missed_probability >= 70:
        risk_level = "High"

    elif missed_probability >= 40:
        risk_level = "Medium"

    else:
        risk_level = "Low"

    print(
        "Risk Level:",
        risk_level
    )

    # ==================================================
    # SAVE PREDICTION
    # ==================================================

    prediction = Prediction(
        user_id=user.user_id,
        missed_probability=missed_probability,
        risk_level=risk_level
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    print(
        "Prediction saved:",
        prediction.prediction_id
    )

    return prediction


@app.get(
    "/predictions",
    response_model=list[PredictionResponse]
)
def get_predictions(
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    user = get_logged_in_profile(
        current_user,
        db
    )

    predictions = db.query(
        Prediction
    ).filter(
        Prediction.user_id == user.user_id
    ).order_by(
        Prediction.prediction_date.desc()
    ).all()

    return predictions


@app.get(
    "/predictions/{prediction_id}",
    response_model=PredictionResponse
)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    user = get_logged_in_profile(
        current_user,
        db
    )

    prediction = db.query(
        Prediction
    ).filter(
        Prediction.prediction_id == prediction_id,
        Prediction.user_id == user.user_id
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=404,
            detail="Prediction not found"
        )

    return prediction


# ==================================================
# USER SUMMARY
# ==================================================

@app.get("/users/{user_id}/summary")
def get_user_summary(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    user = get_logged_in_profile(
        current_user,
        db
    )

    # Security check
    if user.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to access this user's summary"
        )

    records = db.query(
        VaccinationRecord
    ).filter(
        VaccinationRecord.user_id == user.user_id
    ).order_by(
        VaccinationRecord.vaccination_date.asc()
    ).all()

    latest_prediction = db.query(
        Prediction
    ).filter(
        Prediction.user_id == user.user_id
    ).order_by(
        Prediction.prediction_date.desc()
    ).first()

    vaccination_history = []

    for record in records:

        vaccination_history.append({
            "record_id": record.record_id,

            "vaccine_name": (
                record.vaccine.vaccine_name
                if record.vaccine
                else None
            ),

            "dose_number": record.dose_number,

            "vaccination_date":
                record.vaccination_date,

            "next_due_date":
                record.next_due_date,

            "status":
                record.status
        })

    return {
        "user": {
            "user_id": user.user_id,
            "name": user.name,
            "date_of_birth": user.date_of_birth,
            "gender": user.gender,
            "contact": user.contact
        },

        "vaccination_history":
            vaccination_history,

        "latest_prediction": (
            {
                "prediction_id":
                    latest_prediction.prediction_id,

                "missed_probability":
                    latest_prediction.missed_probability,

                "risk_level":
                    latest_prediction.risk_level,

                "prediction_date":
                    latest_prediction.prediction_date
            }
            if latest_prediction
            else None
        )
    }


# ==================================================
# USER PREDICTIONS
# ==================================================

@app.get(
    "/users/{user_id}/predictions",
    response_model=list[PredictionResponse]
)
def get_user_predictions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    user = get_logged_in_profile(
        current_user,
        db
    )

    # Security check
    if user.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to access these predictions"
        )

    predictions = db.query(
        Prediction
    ).filter(
        Prediction.user_id == user.user_id
    ).order_by(
        Prediction.prediction_date.desc()
    ).all()

    return predictions


# ==================================================
# AUTHENTICATION - REGISTER
# ==================================================

@app.post("/auth/register")
def register_user(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    # Check username
    existing_user = db.query(
        AuthUser
    ).filter(
        AuthUser.username == register_data.username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # Basic validation
    if len(register_data.username.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Username must contain at least 3 characters"
        )

    if len(register_data.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters"
        )

    # Hash password
    hashed_password = hash_password(
        register_data.password
    )

    try:

        # ==================================================
        # CREATE AUTH ACCOUNT
        # ==================================================

        auth_user = AuthUser(
            username=register_data.username.strip(),
            password_hash=hashed_password
        )

        db.add(auth_user)
        db.flush()

        # ==================================================
        # CREATE USER PROFILE
        # ==================================================

        user = User(
            auth_user_id=auth_user.auth_user_id,
            name=register_data.name,
            date_of_birth=register_data.date_of_birth,
            gender=register_data.gender,
            contact=register_data.contact
        )

        db.add(user)

        db.commit()

        db.refresh(auth_user)
        db.refresh(user)

        return {
            "message":
                "User registered successfully",

            "auth_user_id":
                auth_user.auth_user_id,

            "user_id":
                user.user_id,

            "username":
                auth_user.username
        }

    except Exception as error:

        db.rollback()

        print(
            "Registration error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to register user"
        )


# ==================================================
# AUTHENTICATION - LOGIN
# ==================================================

@app.post("/auth/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Find authentication user
    auth_user = db.query(
        AuthUser
    ).filter(
        AuthUser.username == form_data.username
    ).first()

    if not auth_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # Verify password
    if not verify_password(
        form_data.password,
        auth_user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # Find connected profile
    user = db.query(
        User
    ).filter(
        User.auth_user_id ==
        auth_user.auth_user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )

    # Create JWT token
    access_token = create_access_token(
        data={
            "sub": auth_user.username,
            "user_id": user.user_id
        }
    )

    return {
        "access_token":
            access_token,

        "token_type":
            "bearer",

        "user_id":
            user.user_id,

        "username":
            auth_user.username
    }


# ==================================================
# AUTHENTICATION - CURRENT USER
# ==================================================

@app.get("/auth/me")
def get_current_user_info(
    current_user: AuthUser = Depends(get_current_user)
):
    return {
        "auth_user_id":
            current_user.auth_user_id,

        "username":
            current_user.username
    }


# ==================================================
# REMINDERS
# ==================================================

@app.get("/users/{user_id}/reminders")
def get_user_reminders(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    user = get_logged_in_profile(
        current_user,
        db
    )

    # Security check
    if user.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to access these reminders"
        )

    records = db.query(
        VaccinationRecord
    ).filter(
        VaccinationRecord.user_id == user.user_id
    ).order_by(
        VaccinationRecord.next_due_date.asc()
    ).all()

    today = date.today()

    reminders = []

    for record in records:

        if not record.next_due_date:
            continue

        if record.next_due_date < today:
            reminder_status = "Overdue"

        elif record.next_due_date == today:
            reminder_status = "Due Today"

        else:
            reminder_status = "Upcoming"

        reminders.append({
            "record_id":
                record.record_id,

            "vaccine_name": (
                record.vaccine.vaccine_name
                if record.vaccine
                else None
            ),

            "dose_number":
                record.dose_number,

            "next_due_date":
                record.next_due_date,

            "status":
                reminder_status
        })

    return {
        "user_id":
            user.user_id,

        "user_name":
            user.name,

        "reminders":
            reminders
    }


# ==================================================
# DASHBOARD
# ==================================================

@app.get("/dashboard/{user_id}")
def get_dashboard(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    # Get logged-in profile
    logged_in_user = get_logged_in_profile(
        current_user,
        db
    )

    # ==================================================
    # SECURITY CHECK
    # ==================================================

    if logged_in_user.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to access this dashboard"
        )

    # ==================================================
    # GET VACCINATION RECORDS
    # ==================================================

    records = db.query(
        VaccinationRecord
    ).filter(
        VaccinationRecord.user_id ==
        logged_in_user.user_id
    ).order_by(
        VaccinationRecord.vaccination_date.asc()
    ).all()

    # ==================================================
    # GET LATEST PREDICTION
    # ==================================================

    latest_prediction = db.query(
        Prediction
    ).filter(
        Prediction.user_id ==
        logged_in_user.user_id
    ).order_by(
        Prediction.prediction_date.desc()
    ).first()

    today = date.today()

    # ==================================================
    # SUMMARY VARIABLES
    # ==================================================

    total_records = len(records)

    completed = 0
    missed = 0
    upcoming = 0
    overdue = 0

    reminders = []

    # ==================================================
    # PROCESS RECORDS
    # ==================================================

    for record in records:

        status = (
            record.status or ""
        ).lower()

        # Completed
        if status == "completed":
            completed += 1

        # Missed
        elif status == "missed":
            missed += 1

        # Dates
        if record.next_due_date:

            # Overdue
            if record.next_due_date < today:

                overdue += 1

                reminders.append({
                    "record_id":
                        record.record_id,

                    "vaccine_name": (
                        record.vaccine.vaccine_name
                        if record.vaccine
                        else None
                    ),

                    "dose_number":
                        record.dose_number,

                    "next_due_date":
                        record.next_due_date,

                    "status":
                        "Overdue"
                })

            # Upcoming
            elif record.next_due_date > today:

                upcoming += 1

                reminders.append({
                    "record_id":
                        record.record_id,

                    "vaccine_name": (
                        record.vaccine.vaccine_name
                        if record.vaccine
                        else None
                    ),

                    "dose_number":
                        record.dose_number,

                    "next_due_date":
                        record.next_due_date,

                    "status":
                        "Upcoming"
                })

            # Due today
            else:

                reminders.append({
                    "record_id":
                        record.record_id,

                    "vaccine_name": (
                        record.vaccine.vaccine_name
                        if record.vaccine
                        else None
                    ),

                    "dose_number":
                        record.dose_number,

                    "next_due_date":
                        record.next_due_date,

                    "status":
                        "Due Today"
                })

    # ==================================================
    # USER DATA
    # ==================================================

    user_data = {
        "user_id":
            logged_in_user.user_id,

        "name":
            logged_in_user.name,

        "date_of_birth":
            logged_in_user.date_of_birth,

        "gender":
            logged_in_user.gender,

        "contact":
            logged_in_user.contact
    }

    # ==================================================
    # VACCINATION SUMMARY
    # ==================================================

    vaccination_summary = {
        "total_records":
            total_records,

        "completed":
            completed,

        "missed":
            missed,

        "upcoming":
            upcoming,

        "overdue":
            overdue
    }

    # ==================================================
    # LATEST PREDICTION
    # ==================================================

    prediction_data = None

    if latest_prediction:

        prediction_data = {
            "prediction_id":
                latest_prediction.prediction_id,

            "missed_probability":
                latest_prediction.missed_probability,

            "risk_level":
                latest_prediction.risk_level,

            "prediction_date":
                latest_prediction.prediction_date
        }

    # ==================================================
    # FINAL DASHBOARD
    # ==================================================

    return {
        "user":
            user_data,

        "vaccination_summary":
            vaccination_summary,

        "latest_prediction":
            prediction_data,

        "reminders":
            reminders
    }
