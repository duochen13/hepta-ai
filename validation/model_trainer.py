"""
Model training and evaluation for validation.

⚠️ MVP: Uses lightweight models (LogisticRegression, LightGBM) for fast iteration.

For production validation, users should provide their own models.
"""

from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from .metrics import compute_metrics


def train_and_evaluate(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    features: List[str],
    label_col: str,
    model_type: str = "logistic",
    class_weights: Optional[Dict[int, float]] = None,
    random_state: int = 42,
) -> Dict[str, float]:
    """
    Train a model and evaluate on test set.

    Args:
        train_df: Training dataframe
        test_df: Test dataframe
        features: List of feature column names
        label_col: Label column name
        model_type: "logistic" or "random_forest"
        class_weights: Optional class weights for imbalanced data
        random_state: Random seed for reproducibility

    Returns:
        Dictionary of metrics (auc, f1, precision, recall, rmse, ne)

    Example:
        >>> features = ["age", "income", "score"]
        >>> metrics = train_and_evaluate(
        ...     train_df, test_df, features, "click",
        ...     model_type="logistic"
        ... )
        >>> print(f"AUC: {metrics['auc']:.3f}")
    """
    # Extract features and labels
    X_train = train_df[features].copy()
    y_train = train_df[label_col].copy()
    X_test = test_df[features].copy()
    y_test = test_df[label_col].copy()

    # Handle missing values (simple median/mode imputation)
    for col in features:
        if X_train[col].isnull().any():
            if X_train[col].dtype in ['int64', 'float64', 'float32', 'int32']:
                fill_value = X_train[col].median()
            else:
                fill_value = X_train[col].mode()[0] if len(X_train[col].mode()) > 0 else "UNKNOWN"

            X_train[col].fillna(fill_value, inplace=True)
            X_test[col].fillna(fill_value, inplace=True)

    # Encode categorical features (simple label encoding)
    for col in features:
        if X_train[col].dtype == 'object':
            # Get all unique values from train
            unique_vals = X_train[col].unique()
            val_to_idx = {val: idx for idx, val in enumerate(unique_vals)}

            # Encode train
            X_train[col] = X_train[col].map(val_to_idx)

            # Encode test (unknown values → -1)
            X_test[col] = X_test[col].map(val_to_idx).fillna(-1).astype(int)

    # Prepare sample weights
    sample_weight = None
    if class_weights is not None:
        sample_weight = y_train.map(class_weights).values

    # Train model
    if model_type == "logistic":
        model = LogisticRegression(
            max_iter=1000,
            random_state=random_state,
            class_weight='balanced' if class_weights is None else None,
        )
    elif model_type == "random_forest":
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=random_state,
            class_weight='balanced' if class_weights is None else None,
        )
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    # Fit
    model.fit(X_train, y_train, sample_weight=sample_weight)

    # Predict
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    # Compute metrics
    metrics = compute_metrics(y_test.values, y_pred, y_pred_proba)

    return metrics


def quick_validation(
    df: pd.DataFrame,
    features: List[str],
    label_col: str,
    test_size: float = 0.2,
    model_type: str = "logistic",
    random_state: int = 42,
) -> Dict[str, float]:
    """
    Quick train/test split validation on a single dataframe.

    Useful for rapid iteration when you don't have a separate test set.

    Args:
        df: Full dataframe
        features: Feature column names
        label_col: Label column name
        test_size: Fraction of data to use for testing
        model_type: "logistic" or "random_forest"
        random_state: Random seed

    Returns:
        Dictionary of metrics

    Example:
        >>> metrics = quick_validation(df, features, "click")
        >>> print(f"AUC: {metrics['auc']:.3f}")
    """
    # Split
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df[label_col] if len(df[label_col].unique()) > 1 else None,
    )

    # Train and evaluate
    return train_and_evaluate(
        train_df,
        test_df,
        features,
        label_col,
        model_type=model_type,
        random_state=random_state,
    )


# Future: Support for custom models (v0.2+)
"""
Example future implementation:

def train_and_evaluate_custom(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    features: List[str],
    label_col: str,
    model: Any,  # User-provided sklearn/lightgbm/xgboost model
    class_weights: Optional[Dict[int, float]] = None,
) -> Dict[str, float]:
    '''
    Train user's custom model and evaluate.

    This allows users to validate with their production models:
    - LightGBM
    - XGBoost
    - CatBoost
    - Neural networks (Keras/PyTorch)

    Example:
        >>> import lightgbm as lgb
        >>> model = lgb.LGBMClassifier(n_estimators=500, learning_rate=0.05)
        >>> metrics = train_and_evaluate_custom(
        ...     train, test, features, "click", model
        ... )
    '''
    pass
"""
