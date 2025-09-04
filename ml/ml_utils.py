"""
ML Utilities - Numpy/Pandas equivalents for scikit-learn functionality
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Optional

def train_test_split(X: np.ndarray, y: np.ndarray, test_size: float = 0.2, 
                    random_state: Optional[int] = None, stratify: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Custom train_test_split function using numpy/pandas
    
    Args:
        X: Feature matrix
        y: Target vector
        test_size: Proportion of data to use for testing
        random_state: Random seed for reproducibility
        stratify: For stratified sampling (not fully implemented)
    
    Returns:
        X_train, X_test, y_train, y_test
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    n_samples = X.shape[0]
    indices = np.arange(n_samples)
    
    if stratify is not None:
        # Simple stratified sampling
        unique_labels, label_counts = np.unique(stratify, return_counts=True)
        train_indices = []
        test_indices = []
        
        for label, count in zip(unique_labels, label_counts):
            label_indices = indices[stratify == label]
            np.random.shuffle(label_indices)
            
            split_idx = int(count * (1 - test_size))
            train_indices.extend(label_indices[:split_idx])
            test_indices.extend(label_indices[split_idx:])
        
        train_indices = np.array(train_indices)
        test_indices = np.array(test_indices)
    else:
        # Random sampling
        np.random.shuffle(indices)
        split_idx = int(n_samples * (1 - test_size))
        train_indices = indices[:split_idx]
        test_indices = indices[split_idx:]
    
    return X[train_indices], X[test_indices], y[train_indices], y[test_indices]

class StandardScaler:
    """
    Custom StandardScaler using numpy/pandas
    """
    
    def __init__(self):
        self.mean_ = None
        self.scale_ = None
        self.fitted_ = False
    
    def fit(self, X: np.ndarray) -> 'StandardScaler':
        """Compute the mean and std to be used for later scaling"""
        self.mean_ = np.mean(X, axis=0)
        self.scale_ = np.std(X, axis=0)
        # Handle zero variance features
        self.scale_[self.scale_ == 0] = 1.0
        self.fitted_ = True
        return self
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Scale features by removing the mean and scaling to unit variance"""
        if not self.fitted_:
            raise ValueError("StandardScaler must be fitted before transform")
        
        X_centered = X - self.mean_
        X_scaled = X_centered / self.scale_
        return X_scaled
    
    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Fit to data, then transform it"""
        return self.fit(X).transform(X)
    
    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Scale back the data to the original representation"""
        if not self.fitted_:
            raise ValueError("StandardScaler must be fitted before inverse_transform")
        
        return X * self.scale_ + self.mean_

class RandomForestClassifier:
    """
    Simplified RandomForestClassifier using numpy/pandas
    Note: This is a basic implementation for demonstration purposes
    """
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 10, 
                 random_state: Optional[int] = None, class_weight: Optional[str] = None):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.class_weight = class_weight
        self.trees = []
        self.classes_ = None
        self.fitted_ = False
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'RandomForestClassifier':
        """Train the random forest model"""
        if self.random_state is not None:
            np.random.seed(self.random_state)
        
        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        
        # For simplicity, we'll use a basic decision tree approach
        # In production, you might want to implement proper random forest
        self.trees = [self._create_tree(X, y) for _ in range(self.n_estimators)]
        self.fitted_ = True
        return self
    
    def _create_tree(self, X: np.ndarray, y: np.ndarray) -> dict:
        """Create a simple decision tree node"""
        if len(np.unique(y)) == 1:
            return {'type': 'leaf', 'prediction': y[0]}
        
        if X.shape[1] == 0:
            return {'type': 'leaf', 'prediction': np.bincount(y).argmax()}
        
        # Simple split on first feature
        feature_idx = 0
        feature_values = X[:, feature_idx]
        split_value = np.median(feature_values)
        
        left_mask = feature_values <= split_value
        right_mask = ~left_mask
        
        if not np.any(left_mask) or not np.any(right_mask):
            return {'type': 'leaf', 'prediction': np.bincount(y).argmax()}
        
        return {
            'type': 'split',
            'feature_idx': feature_idx,
            'split_value': split_value,
            'left': self._create_tree(X[left_mask], y[left_mask]),
            'right': self._create_tree(X[right_mask], y[right_mask])
        }
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels for samples in X"""
        if not self.fitted_:
            raise ValueError("RandomForestClassifier must be fitted before predict")
        
        predictions = []
        for sample in X:
            sample_preds = []
            for tree in self.trees:
                sample_preds.append(self._predict_sample(sample, tree))
            # Majority vote
            predictions.append(np.bincount(sample_preds).argmax())
        
        return np.array(predictions)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities for samples in X"""
        if not self.fitted_:
            raise ValueError("RandomForestClassifier must be fitted before predict_proba")
        
        predictions = []
        for sample in X:
            sample_preds = []
            for tree in self.trees:
                sample_preds.append(self._predict_sample(sample, tree))
            
            # Calculate probabilities
            unique_preds, counts = np.unique(sample_preds, return_counts=True)
            proba = np.zeros(len(self.classes_))
            for pred, count in zip(unique_preds, counts):
                pred_idx = np.where(self.classes_ == pred)[0][0]
                proba[pred_idx] = count / len(sample_preds)
            predictions.append(proba)
        
        return np.array(predictions)
    
    def _predict_sample(self, sample: np.ndarray, tree: dict) -> int:
        """Predict for a single sample using a tree"""
        if tree['type'] == 'leaf':
            return tree['prediction']
        
        if sample[tree['feature_idx']] <= tree['split_value']:
            return self._predict_sample(sample, tree['left'])
        else:
            return self._predict_sample(sample, tree['right'])

def accuracy_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate accuracy score"""
    return np.mean(y_true == y_pred)

def classification_report(y_true: np.ndarray, y_pred: np.ndarray, 
                        target_names: Optional[List[str]] = None) -> str:
    """Generate a simple classification report"""
    if target_names is None:
        target_names = [f"Class {i}" for i in range(len(np.unique(y_true)))]
    
    # Calculate basic metrics
    accuracy = accuracy_score(y_true, y_pred)
    
    report = f"Classification Report:\n"
    report += f"Accuracy: {accuracy:.4f}\n\n"
    
    # Per-class metrics
    unique_labels = np.unique(y_true)
    for i, label in enumerate(unique_labels):
        if i < len(target_names):
            class_name = target_names[i]
        else:
            class_name = f"Class {label}"
        
        mask = y_true == label
        tp = np.sum((y_true == label) & (y_pred == label))
        fp = np.sum((y_true != label) & (y_pred == label))
        fn = np.sum((y_true == label) & (y_pred != label))
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        report += f"{class_name}:\n"
        report += f"  Precision: {precision:.4f}\n"
        report += f"  Recall: {recall:.4f}\n"
        report += f"  F1-Score: {f1:.4f}\n\n"
    
    return report

def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """Calculate confusion matrix"""
    unique_labels = np.unique(np.concatenate([y_true, y_pred]))
    n_labels = len(unique_labels)
    
    cm = np.zeros((n_labels, n_labels), dtype=int)
    
    for i, true_label in enumerate(unique_labels):
        for j, pred_label in enumerate(unique_labels):
            cm[i, j] = np.sum((y_true == true_label) & (y_pred == pred_label))
    
    return cm
