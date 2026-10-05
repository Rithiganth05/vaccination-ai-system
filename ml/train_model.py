import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

import joblib


# Load dataset
data = pd.read_csv("ml/data/vaccination_dataset.csv")

# Features
X = data[
    [
        "age",
        "dose_number",
        "days_late",
        "previous_missed",
        "total_doses"
    ]
]

# Target
y = data["missed"]


# Split data into training and testing
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


# Create the model
model = LogisticRegression()


# Train the model
model.fit(X_train, y_train)


# Make predictions
y_pred = model.predict(X_test)


# Calculate accuracy
accuracy = accuracy_score(y_test, y_pred)

print("Model trained successfully")
print("Accuracy:", accuracy)


# Save the trained model
joblib.dump(
    model,
    "ml/vaccination_model.pkl"
)

print("Model saved successfully")