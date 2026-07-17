"""
Ethio-Agri Advisor - Model Training
Random Forest classifier with feature importance for crop recommendation
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.impute import SimpleImputer
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

class CropModelTrainer:
    """Train and evaluate Random Forest model for crop recommendation"""
    
    def __init__(self, data_path='data/training_data.csv'):
        self.data_path = data_path
        self.model = None
        self.feature_importance = None
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_names = []
        
    def load_data(self):
        """Load and preprocess training data"""
        print("Loading training data...")
        
        if os.path.exists(self.data_path):
            df = pd.read_csv(self.data_path)
        else:
            # Generate sample data if file doesn't exist
            from data_pipeline import AgriDataPipeline
            pipeline = AgriDataPipeline()
            df = pipeline.prepare_training_data(1000)
            os.makedirs('data', exist_ok=True)
            df.to_csv(self.data_path, index=False)
        
        print(f"Loaded {len(df)} samples")
        return df
    
    def preprocess_data(self, df):
        """Preprocess features and encode categorical variables"""
        print("🔧 Preprocessing data...")
        
        # Features and target
        features = ['temperature', 'rainfall', 'soil_ph', 'growing_days', 
                   'soil_type', 'region']
        target = 'crop'
        
        X = df[features].copy()
        y = df[target].copy()
        
        # Encode categorical variables
        categorical_cols = ['soil_type', 'region']
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col])
            self.label_encoders[col] = le
        
        # Handle missing values
        imputer = SimpleImputer(strategy='median')
        X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)
        
        # Scale numerical features
        numerical_cols = ['temperature', 'rainfall', 'soil_ph', 'growing_days']
        X[numerical_cols] = self.scaler.fit_transform(X[numerical_cols])
        
        # Encode target
        le_target = LabelEncoder()
        y_encoded = le_target.fit_transform(y)
        self.label_encoders['target'] = le_target
        
        self.feature_names = X.columns.tolist()
        
        print(f"Preprocessed {len(X)} samples with {len(X.columns)} features")
        return X, y_encoded
    
    def train_model(self, X, y):
        """Train Random Forest classifier with hyperparameter tuning"""
        print("Training Random Forest model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Random Forest with optimized parameters
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            class_weight='balanced',
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Model trained with {accuracy:.2%} accuracy")
        
        # Detailed metrics
        print("\nClassification Report:")
        target_names = self.label_encoders['target'].classes_
        print(classification_report(y_test, y_pred, target_names=target_names))
        
        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 5 Important Features:")
        print(self.feature_importance.head())
        
        return self.model, X_test, y_test, y_pred
    
    def plot_feature_importance(self):
        """Visualize feature importance"""
        if self.feature_importance is None:
            return
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=self.feature_importance.head(10), 
                   x='importance', y='feature')
        plt.title('Top 10 Feature Importance - Crop Recommendation')
        plt.xlabel('Importance Score')
        plt.tight_layout()
        
        # Save plot
        os.makedirs('plots', exist_ok=True)
        plt.savefig('plots/feature_importance.png')
        plt.show()
        
    def save_model(self, model_path='models/crop_model.pkl'):
        """Save trained model and encoders"""
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        model_artifacts = {
            'model': self.model,
            'label_encoders': self.label_encoders,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance,
            'training_date': datetime.now().isoformat()
        }
        
        joblib.dump(model_artifacts, model_path)
        print(f"Model saved to {model_path}")
        
    def load_model(self, model_path='models/crop_model.pkl'):
        """Load trained model"""
        if os.path.exists(model_path):
            artifacts = joblib.load(model_path)
            self.model = artifacts['model']
            self.label_encoders = artifacts['label_encoders']
            self.scaler = artifacts['scaler']
            self.feature_names = artifacts['feature_names']
            self.feature_importance = artifacts.get('feature_importance')
            print(f"Model loaded from {model_path}")
            return True
        else:
            print(f"Model file not found: {model_path}")
            return False
    
    def predict_crop(self, features):
        """
        Predict crop for new data
        features: dict with keys: temperature, rainfall, soil_ph, 
                 growing_days, soil_type, region
        """
        if self.model is None:
            print("No model loaded. Train or load a model first.")
            return None
        
        # Convert features to DataFrame
        df = pd.DataFrame([features])
        
        # Encode categorical features
        for col in ['soil_type', 'region']:
            if col in df.columns and col in self.label_encoders:
                df[col] = self.label_encoders[col].transform(df[col])
        
        # Scale numerical features
        numerical_cols = ['temperature', 'rainfall', 'soil_ph', 'growing_days']
        df[numerical_cols] = self.scaler.transform(df[numerical_cols])
        
        # Predict
        prediction = self.model.predict(df)
        crop = self.label_encoders['target'].inverse_transform(prediction)[0]
        
        # Get probabilities
        probs = self.model.predict_proba(df)[0]
        confidence = max(probs)
        
        # Get feature contributions for this prediction
        if hasattr(self.model, 'feature_importances_'):
            # Local interpretation using SHAP-like approach
            feature_contrib = self.feature_importance.copy()
        
        return {
            'crop': crop,
            'confidence': confidence,
            'recommendations': self._get_recommendations(crop, features)
        }
    
    def _get_recommendations(self, crop, features):
        """Generate actionable recommendations"""
        recommendations = {
            'Teff': {
                'planting': 'Plant at the onset of Belg rains (Feb-Mar)',
                'fertilizer': 'Apply 50kg N/ha and 20kg P/ha',
                'irrigation': 'Supplement with irrigation if rainfall < 600mm',
                'harvest': 'Harvest when leaves turn yellow (90-100 days)'
            },
            'Wheat': {
                'planting': 'Plant in June-July for Meher season',
                'fertilizer': 'Apply 60kg N/ha and 30kg P/ha',
                'irrigation': 'Requires well-distributed rainfall',
                'harvest': 'Harvest when heads turn golden (110-120 days)'
            },
            'Maize': {
                'planting': 'Plant after heavy rains (April-May)',
                'fertilizer': 'Apply 100kg N/ha and 40kg P/ha',
                'irrigation': 'Critical during tasseling stage',
                'harvest': 'Harvest when husks dry (120-140 days)'
            },
            'Coffee': {
                'planting': 'Plant with shade trees, start of rainy season',
                'fertilizer': 'Apply organic manure, 20-20-20 NPK',
                'irrigation': 'Maintain even moisture, avoid waterlogging',
                'harvest': 'Harvest red berries (October-December)'
            }
        }
        
        return recommendations.get(crop, {
            'planting': 'Consult local agricultural office',
            'fertilizer': 'Conduct soil test for specific recommendations',
            'irrigation': 'Based on rainfall pattern',
            'harvest': 'Monitor crop maturity'
        })

# Main training script
if __name__ == "__main__":
    print("Starting model training...")
    
    trainer = CropModelTrainer()
    
    # Load and preprocess
    df = trainer.load_data()
    X, y = trainer.preprocess_data(df)
    
    # Train model
    model, X_test, y_test, y_pred = trainer.train_model(X, y)
    
    # Visualize feature importance
    trainer.plot_feature_importance()
    
    # Save model
    trainer.save_model()
    
    print("\n🎉 Training complete! Model is ready for deployment.")
