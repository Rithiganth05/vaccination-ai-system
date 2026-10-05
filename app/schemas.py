from pydantic import BaseModel
from datetime import date,datetime


class UserCreate(BaseModel):
    name: str
    date_of_birth: date
    gender: str
    contact: str

class UserResponse(BaseModel):
    user_id: int
    name: str
    date_of_birth: date
    gender: str
    contact: str
    created_at: datetime    

class VaccineCreate(BaseModel):
    vaccine_name: str
    description: str   

class VaccineUpdate(BaseModel):
    vaccine_name: str
    description: str | None = None  

class VaccineResponse(BaseModel):
    vaccine_id: int
    vaccine_name: str
    description: str | None = None       

class VaccinationRecordCreate(BaseModel):
    user_id: int
    vaccine_id: int
    dose_number: int
    vaccination_date: date
    next_due_date: date | None = None
    status: str    

class VaccinationRecordUpdate(BaseModel):
    user_id: int
    vaccine_id: int
    dose_number: int
    vaccination_date: date
    next_due_date: date | None = None
    status: str

class VaccinationRecordResponse(BaseModel):
    record_id: int
    user_id: int
    vaccine_id: int
    dose_number: int
    vaccination_date: date
    next_due_date: date | None = None
    status: str    

class PredictionCreate(BaseModel):
    user_id: int

class PredictionResponse(BaseModel):
    prediction_id: int
    user_id: int
    missed_probability: float
    risk_level: str
    prediction_date: datetime    

class RegisterRequest(BaseModel):

    username: str
    password: str

    name: str
    date_of_birth: date
    gender: str
    contact: str