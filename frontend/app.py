import streamlit as st
import requests

st.title("Titanic Survival Prediction")

# Create input form
with st.form("prediction_form"):
    passengerid = st.number_input("Passenger ID", min_value=1, step=1)
    pclass = st.selectbox("Pclass", [1, 2, 3])
    sex = st.selectbox("Sex", ["male", "female"])
    age = st.number_input("Age", min_value=0.0, step=0.1)
    fare = st.number_input("Fare", min_value=0.0, step=0.1)
    embarked = st.selectbox("Embarked", ["S", "C", "Q"])
    sibsp = st.number_input("Siblings/Spouse aboard (sibsp)", min_value=0, step=1)
    parch = st.number_input("Parents/Children aboard (parch)", min_value=0, step=1)
    cabin = st.text_input("Cabin (optional)")
    name = st.text_input("Name (e.g., Smith, Mr. John)", value="Smith, Mr. John")

    submit = st.form_submit_button("Predict")

if submit:
    # Construct request payload
    payload = {
        "passengerid": passengerid,
        "pclass": pclass,
        "sex": sex,
        "age": age,
        "fare": fare,
        "embarked": embarked,
        "sibsp": sibsp,
        "parch": parch,
        "cabin": cabin,
        "name": name
    }

    # Replace with your actual FastAPI endpoint
    #FASTAPI_URL = "http://127.0.0.1:8000/predict"
    #response = requests.post("/predict", json=input_data)


    try:
        response = requests.post("http://nginx:90/predict", json=payload)

        response.raise_for_status()
        result = response.json()

        prediction = result.get("prediction")
        st.success(f"Prediction: {'Survived' if prediction == 1 else 'Did Not Survive'}")

    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
