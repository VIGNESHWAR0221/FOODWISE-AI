# FOODWISE AI — Smart Food Demand & Waste Prevention System

## Quick start

### 1. Backend
Open a terminal in `backend`:

Windows:
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at:
http://127.0.0.1:8000

Swagger API documentation:
http://127.0.0.1:8000/docs

### 2. Frontend
From the `frontend` folder, start a simple web server.

If Python is installed:
```powershell
python -m http.server 5500
```

Open:
http://127.0.0.1:5500

Do not open index.html directly with file:// because browser CORS/module/security behavior can cause problems.

## 3. First test
1. Start backend.
2. Open frontend.
3. Open Prediction.
4. Enter attendance and weather values.
5. Click Predict Demand.
6. Open Consumption and save actual consumption.
7. Open Waste and save a waste record.
8. Open Analytics.
9. Open What-If and test another attendance scenario.

## 4. Model
The first run automatically trains:
- Random Forest demand model
- XGBoost waste model
- Linear Regression baseline

Models are stored in `backend/ml/*.pkl`.

## 5. Important
The included CSV is synthetic development data. Do not present it as real institutional data.

## 6. Firebase
The current starter uses a local JSON store so the complete demo can run immediately. For final cloud deployment, replace `backend/services/storage.py` with a Firestore adapter and keep credentials in environment variables.

## 7. Next production improvements
- Firebase Firestore adapter
- Real weather API
- Authentication
- SHAP explanations
- Scheduled model retraining
- Ingredient recipe management UI
- Better real-time monitoring
- Role-based access
- Cloud deployment
