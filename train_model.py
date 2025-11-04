import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
import joblib

CSV_PATH = "synthetic_dataset.csv"
MODEL_PATH = "model.pkl"
ENCODERS_PATH = "encoders.pkl"
RANDOM_STATE = 42

def main():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"{CSV_PATH} not found. Please make sure it exists in the backend folder.")

    print("📂 Loading synthetic dataset...")
    df = pd.read_csv(CSV_PATH)

    if 'label' not in df.columns:
        raise ValueError("Dataset must contain a 'label' column indicating ransomware (1) or benign (0).")

    print(f"✅ Loaded dataset with {len(df)} samples and {len(df.columns)} columns.")

    # Split features and label
    X = df.drop(columns=['label'])
    y = df['label']

    # Handle categorical encoding
    encoders = {}
    if 'extension' in X.columns:
        le = LabelEncoder()
        X['extension'] = le.fit_transform(X['extension'].astype(str))
        encoders['extension'] = le

    # Ensure all features are numeric
    X = X.apply(pd.to_numeric, errors='coerce').fillna(0)

    # Split the dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y)

    # Train RandomForest model
    print("🚀 Training RandomForest model...")
    model = RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"✅ Training complete. Test accuracy: {acc*100:.2f}%")
    print("📊 Classification report:\n", classification_report(y_test, y_pred))

    # Save model and encoders
    joblib.dump(model, MODEL_PATH)
    joblib.dump(encoders, ENCODERS_PATH)
    print(f"💾 Model saved -> {MODEL_PATH}")
    print(f"💾 Encoders saved -> {ENCODERS_PATH}")

if __name__ == "__main__":
    main()
