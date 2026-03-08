# ml_model_manager.py — ML Model Persistence & Continuous Learning

import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Tuple, Dict, Optional, List
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from pathlib import Path
import joblib
from logger_system import get_logger, log_ml_event, log_error
from storage_manager import get_storage_manager

class MLModelManager:
    """Manages ML model training, validation, persistence, and continuous learning"""
    
    def __init__(self, model_name: str = "InvestmentPredictor", model_type: str = "rf"):
        """
        Initialize ML model manager
        
        Args:
            model_name: Name of the model
            model_type: 'rf' for RandomForest, 'gb' for GradientBoosting
        """
        self.model_name = model_name
        self.model_type = model_type
        self.logger = get_logger()
        self.storage = get_storage_manager()
        
        # Model components
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.training_history = []
        self.performance_metrics = {}
        
        # Load existing model if available
        self._load_model()
    
    def _load_model(self):
        """Load previously trained model from storage"""
        try:
            # Try to load with joblib first (faster)
            model_dir = Path("./data/ml_models")
            model_dir.mkdir(exist_ok=True)
            
            model_files = list(model_dir.glob(f"{self.model_name}_model_*.pkl"))
            if model_files:
                latest_model = sorted(model_files, reverse=True)[0]
                data = pickle.load(open(latest_model, 'rb'))
                
                self.model = data['model']
                self.scaler = data['scaler']
                self.feature_names = data['feature_names']
                self.training_history = data.get('training_history', [])
                
                self.logger.info(f"Model loaded: {latest_model.name}")
                return
            
            self.logger.info(f"No existing model found, will train new one")
            self._initialize_model()
        except Exception as e:
            log_error("_load_model", e, f"model={self.model_name}")
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize a new model"""
        try:
            if self.model_type == "gb":
                self.model = GradientBoostingClassifier(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=6,
                    random_state=42
                )
            else:  # Default to RandomForest
                self.model = RandomForestClassifier(
                    n_estimators=200,
                    max_depth=15,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                )
            
            self.scaler = StandardScaler()
            self.logger.info(f"Model initialized: {self.model_type}")
        except Exception as e:
            log_error("_initialize_model", e, f"model_type={self.model_type}")
    
    def prepare_features(self, market_data: pd.DataFrame, feature_list: List[str] = None) -> Tuple[np.ndarray, List[str]]:
        """
        Prepare and scale features for model
        
        Args:
            market_data: DataFrame with market data
            feature_list: List of feature columns to use
        
        Returns:
            Tuple of (scaled_features, feature_names)
        """
        try:
            if feature_list is None:
                # Auto-select numeric features
                feature_list = [
                    'Price', 'RSI', 'MA50', 'MA200', 'above_ma50', 'above_ma200',
                    'ret_5d', 'ret_20d', 'bb_width', 'macd', 'momentum',
                    'volatility', 'vol_ratio', 'DivYield', 'Margin', 'ROE',
                    'EarnGrowth', 'RevGrowth', 'Safety', 'FairValue'
                ]
            
            # Filter to available features
            available_features = [f for f in feature_list if f in market_data.columns]
            
            if len(available_features) == 0:
                self.logger.error(f"No features available for training")
                return np.array([]), []
            
            X = market_data[available_features].fillna(0)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            self.feature_names = available_features
            
            self.logger.info(f"Features prepared: {len(available_features)} features")
            return X_scaled, available_features
        except Exception as e:
            log_error("prepare_features", e, f"columns={len(market_data.columns)}")
            return np.array([]), []
    
    def train(self, X: np.ndarray, y: np.ndarray, validation_split: float = 0.2) -> Dict:
        """
        Train model with cross-validation
        
        Args:
            X: Feature matrix
            y: Target labels (0: HOLD/SELL, 1: BUY)
            validation_split: Portion for validation
        
        Returns:
            Training metrics dictionary
        """
        try:
            if len(X) < 10:
                self.logger.warning(f"Not enough data for training: {len(X)} samples")
                return {}
            
            # Train/validation split
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Validation scores
            train_score = self.model.score(X_train, y_train)
            val_score = self.model.score(X_val, y_val)
            
            # Cross-validation
            cv_scores = cross_val_score(self.model, X, y, cv=5)
            
            metrics = {
                'accuracy': float(val_score),
                'train_accuracy': float(train_score),
                'cv_mean': float(cv_scores.mean()),
                'cv_std': float(cv_scores.std()),
                'training_samples': len(X),
                'timestamp': datetime.now().isoformat()
            }
            
            # Save metrics
            self.storage.save_ml_metrics(self.model_name, metrics)
            
            # Update history
            self.training_history.append(metrics)
            
            # Save model
            self._save_model()
            
            log_ml_event(self.model_name, "Training complete", 
                        f"Accuracy: {val_score:.4f}, CV: {cv_scores.mean():.4f}±{cv_scores.std():.4f}")
            
            self.performance_metrics = metrics
            return metrics
        except Exception as e:
            log_error("train", e, f"X_shape={X.shape}, y_shape={y.shape}")
            return {}
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions on new data
        
        Returns:
            Tuple of (predictions, probabilities)
        """
        try:
            if self.model is None:
                self.logger.warning("Model not trained yet")
                return np.array([]), np.array([])
            
            # Ensure same number of features
            if X.shape[1] != len(self.feature_names):
                self.logger.warning(f"Feature mismatch: expected {len(self.feature_names)}, got {X.shape[1]}")
                return np.array([]), np.array([])
            
            predictions = self.model.predict(X)
            probabilities = self.model.predict_proba(X)[:, 1]  # Probability of class 1 (BUY)
            
            return predictions, probabilities
        except Exception as e:
            log_error("predict", e, f"X_shape={X.shape}")
            return np.array([]), np.array([])
    
    def get_feature_importance(self, top_n: int = 10) -> Dict[str, float]:
        """Get most important features"""
        try:
            if self.model is None or not hasattr(self.model, 'feature_importances_'):
                return {}
            
            importances = self.model.feature_importances_
            feature_importance = dict(zip(self.feature_names, importances))
            
            # Sort by importance
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            
            return dict(sorted_features[:top_n])
        except Exception as e:
            log_error("get_feature_importance", e, "")
            return {}
    
    def evaluate_on_test_set(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """
        Evaluate model on test set
        
        Returns:
            Detailed evaluation metrics
        """
        try:
            from sklearn.metrics import (
                accuracy_score, precision_score, recall_score, f1_score,
                confusion_matrix, roc_auc_score, classification_report
            )
            
            if self.model is None:
                return {}
            
            predictions = self.model.predict(X_test)
            probabilities = self.model.predict_proba(X_test)[:, 1]
            
            metrics = {
                'accuracy': float(accuracy_score(y_test, predictions)),
                'precision': float(precision_score(y_test, predictions, zero_division=0)),
                'recall': float(recall_score(y_test, predictions, zero_division=0)),
                'f1_score': float(f1_score(y_test, predictions, zero_division=0)),
                'roc_auc': float(roc_auc_score(y_test, probabilities)),
                'confusion_matrix': confusion_matrix(y_test, predictions).tolist(),
                'test_samples': len(X_test)
            }
            
            self.logger.info(f"Test set evaluation: {metrics}")
            return metrics
        except Exception as e:
            log_error("evaluate_on_test_set", e, "")
            return {}
    
    def _save_model(self):
        """Save model to storage"""
        try:
            model_dir = Path("./data/ml_models")
            model_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_path = model_dir / f"{self.model_name}_model_{timestamp}.pkl"
            
            data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'training_history': self.training_history,
                'metrics': self.performance_metrics
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(data, f)
            
            self.logger.info(f"Model saved: {model_path}")
            return True
        except Exception as e:
            log_error("_save_model", e, f"model={self.model_name}")
            return False
    
    def continuous_learning(self, new_data: pd.DataFrame, new_labels: np.ndarray) -> Dict:
        """
        Perform continuous learning with new data
        Good for agent learning from recent trades
        
        Args:
            new_data: New market data
            new_labels: Labels for new data
        
        Returns:
            Updated metrics
        """
        try:
            # Prepare features
            X_new, _ = self.prepare_features(new_data)
            
            if len(X_new) == 0:
                return {}
            
            # Retrain with new data
            if self.model is None:
                self._initialize_model()
            
            # Add new data to history
            self.training_history.append({
                'type': 'continuous_learning',
                'samples': len(new_data),
                'timestamp': datetime.now().isoformat()
            })
            
            # Retrain
            metrics = self.train(X_new, new_labels)
            
            log_ml_event(self.model_name, "Continuous learning", 
                        f"Updated with {len(new_data)} new samples")
            
            return metrics
        except Exception as e:
            log_error("continuous_learning", e, f"samples={len(new_data)}")
            return {}
    
    def get_model_info(self) -> Dict:
        """Get model information and statistics"""
        return {
            'model_name': self.model_name,
            'model_type': self.model_type,
            'features_count': len(self.feature_names),
            'feature_names': self.feature_names,
            'training_sessions': len(self.training_history),
            'performance_metrics': self.performance_metrics,
            'last_trained': self.training_history[-1].get('timestamp') if self.training_history else None
        }

# Global instance
_model_manager = None

def get_model_manager(model_name: str = "InvestmentPredictor") -> MLModelManager:
    """Get or create model manager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = MLModelManager(model_name)
    return _model_manager

# Example usage:
"""
from ml_model_manager import get_model_manager

manager = get_model_manager("ValuePredictorV2")

# Prepare data
X, features = manager.prepare_features(market_data)

# Create labels (1 = BUY, 0 = HOLD/SELL)
y = (market_data['Score'] >= 4).astype(int).values

# Train
metrics = manager.train(X, y)
print(f"Model accuracy: {metrics['accuracy']:.4f}")

# Predict on new data
predictions, probabilities = manager.predict(X_new)

# Get important features
important_features = manager.get_feature_importance()
print(f"Top features: {important_features}")

# Continuous learning from agent's past trades
agent_trades = load_agent_trades()
agent_labels = generate_labels_from_trades(agent_trades)
manager.continuous_learning(agent_trades, agent_labels)

# Model info
print(manager.get_model_info())
"""
