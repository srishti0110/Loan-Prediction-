import os
import joblib
import numpy as np
import pandas as pd
from pydantic import BaseModel

from fastapi import FastAPI
from mangum import Mangum

# ------------------------------------------------------------------
# STEP 0: Basic setup
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))       # .../api
PROJECT_DIR = os.path.dirname(BASE_DIR)                      # project root

app = FastAPI(title="Loan Approval Prediction API")
handler = Mangum(app)   # required for Vercel serverless deployment

# The exact columns/order the model expects, in a single place.
EXPECTED_COLUMNS = [
    'Gender', 'Married', 'Education', 'Employment_Status',
    'Annual_Income', 'Loan_Amount', 'Loan_Amount_Term',
    'Credit_History', 'Property_Area'
]

# ------------------------------------------------------------------
# STEP 1: Load model + preprocessor (do NOT reload the whole training
# CSV on every cold start -- it's unnecessary for serving predictions
# and will crash the API if the data folder isn't deployed).
# ------------------------------------------------------------------
try:
    preprocessor = joblib.load(os.path.join(BASE_DIR, 'preprocessor.pkl'))
    model = joblib.load(os.path.join(BASE_DIR, 'best_model.pkl'))
except Exception as e:
    preprocessor = None
    model = None
    print(f"Model loading error: {e}")


class PredictRequest(BaseModel):
    # A single row of input, in EXPECTED_COLUMNS order, e.g.:
    # ["Male", "Yes", "Graduate", "Salaried", 50000, 150000, 360, 1.0, "Urban"]
    data: list


@app.get("/api")
def read_root():
    return {"message": "ML Model API is Live!", "model_loaded": model is not None}


@app.post("/api/predict")
def predict(request: PredictRequest):
    if model is None or preprocessor is None:
        return {"error": "Model not loaded"}

    if len(request.data) != len(EXPECTED_COLUMNS):
        return {
            "error": f"Expected {len(EXPECTED_COLUMNS)} values "
                     f"({EXPECTED_COLUMNS}), got {len(request.data)}."
        }

    try:
        # Build a one-row DataFrame from the ACTUAL request payload
        # (previously this used `loan_data`, the whole training set,
        # so every prediction was on row 0 no matter what was sent).
        input_df = pd.DataFrame([request.data], columns=EXPECTED_COLUMNS)

        # Same manual encodings applied to the training data must be
        # applied here too, since the preprocessor was fit on data
        # that already had these mapped to 0/1.
        gender_map = {'Male': 0, 'Female': 1}
        married_map = {'No': 0, 'Yes': 1}
        education_map = {'Not Graduate': 0, 'Graduate': 1}

        input_df['Gender'] = input_df['Gender'].map(gender_map).fillna(input_df['Gender'])
        input_df['Married'] = input_df['Married'].map(married_map).fillna(input_df['Married'])
        input_df['Education'] = input_df['Education'].map(education_map).fillna(input_df['Education'])

        # The preprocessor only transforms these 5 raw columns:
        #   numeric  -> Annual_Income_log, Loan_Amount_log, Loan_Amount_Term
        #   category -> Property_Area, Employment_Status
        # (confirmed directly from preprocessor.pkl / best_model.pkl)
        input_df['Annual_Income'] = input_df['Annual_Income'].astype(float)
        input_df['Loan_Amount'] = input_df['Loan_Amount'].astype(float)
        input_df['Annual_Income_log'] = np.log1p(input_df['Annual_Income'])
        input_df['Loan_Amount_log'] = np.log1p(input_df['Loan_Amount'])

        preproc_input = input_df[[
            'Annual_Income_log', 'Loan_Amount_log', 'Loan_Amount_Term',
            'Property_Area', 'Employment_Status'
        ]]
        transformed = preprocessor.transform(preproc_input)
        transformed_df = pd.DataFrame(
            transformed if not hasattr(transformed, "toarray") else transformed.toarray(),
            columns=preprocessor.get_feature_names_out()
        )

        # The model was trained on those 9 preprocessed columns PLUS
        # these 4 raw manually-encoded columns, concatenated in this
        # exact order (from model.feature_names_in_).
        final_row = pd.concat(
            [transformed_df, input_df[['Gender', 'Married', 'Education', 'Credit_History']].reset_index(drop=True)],
            axis=1
        )
        final_row = final_row[model.feature_names_in_]

        prediction = model.predict(final_row)
        return {"prediction": int(prediction[0])}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("index:app", host="0.0.0.0", port=8000, reload=True)