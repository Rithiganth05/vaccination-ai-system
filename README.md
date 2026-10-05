# Vaccination Tracking & AI Prediction System

## About the Project

This is a full stack project developed using Python, FastAPI, React, PostgreSQL and Machine Learning.

The main purpose of this project is to manage vaccination details of users and predict whether a user may miss a vaccination dose.

The project has a frontend, backend, database and machine learning model.

## Technologies Used

* Python
* FastAPI
* React
* PostgreSQL
* SQLAlchemy
* Alembic
* JWT Authentication
* Pandas
* Scikit-learn
* Git and GitHub

## Main Features

### User Registration

New users can create an account using username and password.

### User Login

Users can login using their registered username and password.

JWT authentication is used to provide secure access to the application.

### Vaccination Records

Users can store and manage their vaccination records.

### Vaccine Management

The system stores vaccine details and dose information.

### Dashboard

After login, the user can view their vaccination information through the React dashboard.

### AI Prediction

The project uses a Machine Learning model to predict whether a vaccination dose may be missed.

The model uses features such as:

* Age
* Dose number
* Days late
* Previous missed doses
* Total doses

## How the Project Works

```text
User
  ↓
React Frontend
  ↓
FastAPI REST API
  ↓
PostgreSQL Database
  ↓
Machine Learning Model
  ↓
Prediction Result
  ↓
React Dashboard
```

## Machine Learning

I created a dataset containing vaccination-related information.

The dataset is processed and used to train a Machine Learning model.

The trained model is saved as:

```text
ml/vaccination_model.pkl
```

The FastAPI backend loads this model and uses it when the user requests a prediction.

## Project Structure

```text
vaccination-ai-system/
│
├── app/
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   └── test_db.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
│
├── alembic/
│
├── ml/
│   ├── data/
│   ├── train_model.py
│   └── vaccination_model.pkl
│
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

## API

The backend is developed using FastAPI.

Some of the APIs are:

* User Registration
* User Login
* Users
* Vaccines
* Vaccination Records
* Predictions
* Dashboard

Swagger documentation can be accessed when the backend is running:

```text
http://127.0.0.1:8001/docs
```

## Database

PostgreSQL is used as the database.

The database stores:

* User details
* Authentication details
* Vaccine details
* Vaccination records
* Prediction details

SQLAlchemy is used to connect the Python application with PostgreSQL.

Alembic is used for database migrations.

## Authentication

JWT authentication is used in this project.

The basic flow is:

```text
User Login
    ↓
Username and Password Verification
    ↓
JWT Token Generated
    ↓
Token Sent with API Request
    ↓
Protected API Access
```

## Frontend

The frontend is developed using React and Vite.

It provides:

* Login
* User authentication
* Dashboard
* Vaccination records
* Vaccine details
* Prediction information
* Logout

## How to Run the Project

### Backend

Create and activate the virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the FastAPI application:

```bash
uvicorn app.main:app --reload --port 8001
```

### Frontend

Go to the frontend folder:

```bash
cd frontend
```

Install the packages:

```bash
npm install
```

Run the frontend:

```bash
npm run dev
```

## Future Improvements

In future, I can improve the project by adding:

* Vaccination reminders
* Email notifications
* Admin dashboard
* Hospital and doctor management
* Better Machine Learning models
* Cloud deployment
* Mobile application

## My Role in the Project

I developed the project by working on the backend, frontend, database, authentication and Machine Learning parts.

I used FastAPI to create REST APIs, PostgreSQL to store the data, React to create the frontend and Scikit-learn to build the prediction model.



Rithiganth A N

AI & Data Science


