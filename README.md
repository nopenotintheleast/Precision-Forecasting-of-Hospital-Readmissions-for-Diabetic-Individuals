# Precision-Forecasting-of-Hospital-Readmissions-for-Diabetic-Individuals

📌 Table of Contents

Project Overview

Key Features

Technical Architecture

Installation & Setup

Usage

Model Performance

Future Enhancements

Contributing

License

References


🔍 Project Overview

Hospital readmissions for diabetic patients are a major healthcare challenge, leading to increased costs and poor patient outcomes. This system leverages machine learning (XGBoost) to predict 30-day readmission risks based on:


Clinical data (HbA1c, medications, comorbidities)

Demographics (age, gender)

Hospitalization history (prior admissions, length of stay)

The web interface allows doctors to:

✅ Input patient data

✅ Get real-time risk predictions (High/Low Risk)

✅ View explainable AI insights (SHAP values)



✨ Key Features

Feature	Description

📊 Predictive Analytics	XGBoost model trained on diabetic patient data

⚖️ Class Balancing	SMOTE oversampling for imbalanced datasets

📈 Interpretable AI	SHAP values & feature importance plots

💻 Web Dashboard	Flask backend + interactive frontend

🔒 Secure & Scalable	Modular design for future EHR integration


🛠️ Technical Architecture
![drrps](https://github.com/user-attachments/assets/dc808d18-ee30-46b1-8a68-a503f3a9a6fc)

Tech Stack

Backend: Python, Flask

Machine Learning: XGBoost, Scikit-learn, SMOTE

Frontend: HTML, CSS, JavaScript, Tailwind CSS

Data Processing: Pandas, NumPy

Visualization: Matplotlib, Seaborn


⚙️ Installation & Setup

Prerequisites

Python 3.9+

pip

Steps

1. Clone the repo

bash
git clone https://github.com/nopenotintheleast/Precision-Forecasting-of-Hospital-Readmissions-for-Diabetic-Individuals.git

cd diabetic-readmission-prediction

2. Install dependencies

bash
pip install -r requirements.txt

4. Run the Flask app

bash
cd backend

python app.py init-db

Access the web app at: http://localhost:5000


📲 Usage

~Enter patient data via the web form.

~Submit to generate a risk prediction.


View results:

~Risk score (High/Low)

~Confidence percentage

~Key influencing factors (e.g., HbA1c, insulin use)


Demo Screenshot
![prediction_success](https://github.com/user-attachments/assets/4db1cac5-8597-4853-ab54-2f90edd95371)


📊 Model Performance

~Metric	Score

~Accuracy	72%

~Precision	61%

~Recall	64%

~F1-Score	62%

~AUC-ROC	0.78

~Confusion Matrix at Optimal Threshold (0.42)



🚀 Future Enhancements

~EHR Integration (HL7/FHIR API)

~Real-time monitoring with IoT devices

~Multi-disease prediction (Heart Failure, COPD)

~Patient-facing dashboard


🤝 Contributing

Contributions are welcome!

~Fork the repo

~Create a branch (git checkout -b feature/your-feature)

~Commit changes (git commit -m "Add your feature")

~Push to branch (git push origin feature/your-feature)

~Open a Pull Request


📜 License

This project is licensed under MIT License.

📚 References

Caruana et al. (2015). Intelligible Models for Healthcare

Chen & Guestrin (2016). XGBoost: A Scalable Tree Boosting System

Lundberg & Lee (2017). SHAP: A Unified Approach to Model Interpretability


🌟 Star this repo if you find it useful!
