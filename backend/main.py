from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd

app = FastAPI()

# Load trained model
try:
    model = joblib.load("artifacts/models/random_forest_model.pkl")
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    raise HTTPException(status_code=500, detail="Model loading failed.")

# Request Schema
class PassengerData(BaseModel):
    passengerid: int
    pclass: int
    sex: str
    age: float
    fare: float
    embarked: str
    sibsp: int
    parch: int
    cabin: str = None
    name: str

@app.post("/predict")
def predict_survival(data: PassengerData):
    try:
        df = pd.DataFrame([data.dict()])

        # --- Preprocessing ---
        df['sex'] = df['sex'].map({'male': 0, 'female': 1})
        df['embarked'] = df['embarked'].astype('category').cat.codes

        df['familysize'] = df['sibsp'] + df['parch'] + 1
        df['islaone'] = (df['familysize'] == 1).astype(int)
        df['hascabin'] = df['cabin'].notnull().astype(int)

        df['title'] = df['name'].str.extract(' ([A-Za-z]+)\.', expand=False).map(
            {'Mr': 0, 'Miss': 1, 'Mrs': 2, 'Master': 3, 'Rare': 4}
        ).fillna(4)

        df['pclass_fare'] = df['pclass'] * df['fare']
        df['age_fare'] = df['age'] * df['fare']

        # Features for prediction (must match training features)
        feature_cols = ['pclass', 'sex', 'age', 'fare', 'embarked',
                        'familysize', 'islaone', 'hascabin', 'title',
                        'pclass_fare', 'age_fare']
        input_data = df[feature_cols]

        prediction = model.predict(input_data)

        return {"passengerid": data.passengerid, "prediction": int(prediction[0])}

    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed.")
