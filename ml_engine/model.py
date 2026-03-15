"""
ML Engine - Scoring models (LightGBM).
"""

import os
import numpy as np
import pandas as pd
import lightgbm as lgb
from typing import Dict, Union

# Exactly the 6 features the LightGBM model was trained on — order matters
MODEL_FEATURES = [
    "revenue_expense_ratio",
    "working_capital",
    "debt_equity_ratio",
    "gst_bank_match_score",
    "legal_flag_count",
    "sector_risk_flag",
]

class CreditScoringModel:
    def __init__(self, reject_threshold: float = 0.7, watchlist_threshold: float = 0.4):
        self.model = None
        self.reject_threshold = reject_threshold
        self.watchlist_threshold = watchlist_threshold

    def load_model(self, path_or_artifact: str):
        """
        Loads a pre-trained LightGBM model from disk.
        If the file doesn't exist, it initializes and trains a mock model for testing purposes.
        """
        if os.path.exists(path_or_artifact):
            try:
                self.model = lgb.Booster(model_file=path_or_artifact)
                return  # Loaded successfully, done.
            except Exception as e:
                print(f"[model.py] Corrupted or incompatible model file at {path_or_artifact}: {e}")
                print("[model.py] Deleting and regenerating a fresh mock model...")
                try:
                    os.remove(path_or_artifact)
                except Exception:
                    pass
        if not os.path.exists(path_or_artifact):
            print(f"Model not found at {path_or_artifact}. Initializing and training new model.")
            
            # Generate 500 training samples
            np.random.seed(42)
            
            # APPROVE cases
            n_app = 300
            app_wc = np.random.uniform(15_000_000, 80_000_000, n_app)
            app_rer = np.random.uniform(0.08, 0.22, n_app)
            app_der = np.random.uniform(0.3, 1.2, n_app)
            app_gst = np.random.uniform(0.60, 0.95, n_app)
            app_lfc = np.zeros(n_app)
            app_srt = np.zeros(n_app)
            
            # WATCHLIST cases
            n_wa = 100
            wa_wc = np.random.uniform(8_000_000, 30_000_000, n_wa)
            wa_rer = np.random.uniform(0.05, 0.12, n_wa)
            wa_der = np.random.uniform(0.9, 1.8, n_wa)
            wa_gst = np.random.uniform(0.45, 0.70, n_wa)
            wa_lfc = np.random.randint(0, 2, n_wa)
            wa_srt = np.random.randint(0, 2, n_wa)
            
            # REJECT cases
            n_rej = 100
            rej_wc = np.random.uniform(-5_000_000, 15_000_000, n_rej)
            rej_rer = np.random.uniform(0.01, 0.09, n_rej)
            rej_der = np.random.uniform(1.2, 3.5, n_rej)
            rej_gst = np.random.uniform(0.20, 0.60, n_rej)
            rej_lfc = np.random.randint(1, 5, n_rej)
            rej_srt = np.random.randint(0, 2, n_rej)
            
            # Combine
            X_app = np.column_stack((app_rer, app_wc, app_der, app_gst, app_lfc, app_srt))
            X_wa = np.column_stack((wa_rer, wa_wc, wa_der, wa_gst, wa_lfc, wa_srt))
            X_rej = np.column_stack((rej_rer, rej_wc, rej_der, rej_gst, rej_lfc, rej_srt))
            
            X = np.vstack((X_app, X_wa, X_rej))
            
            # Add Gaussian noise: +/- 10% roughly
            X = X * np.random.normal(1.0, 0.05, X.shape)
            
            # Explicit rule for labels to enforce correct SHAP directions
            # Col Mapping: 0=rer, 1=wc, 2=der, 3=gst, 4=lfc, 5=srt
            default_probability = (
                - 1.5 * X[:, 3] # Heavily penalize low GST match (high reward for good match)
                + 0.25 * X[:, 2] 
                - 0.2 * (X[:, 1] / 100_000_000.0) 
                + 0.4 * (X[:, 4] / 2.0) # Penalize legal flags more 
                - 0.1 * X[:, 0] 
                + 0.2 * X[:, 5]
                + 0.75 + np.random.normal(0, 0.2, len(X)) # Lower base score (0.75 default risk)
            )
            y = np.where(default_probability > 0.5, 1, 0)
            
            train_data = lgb.Dataset(
                data=X,
                label=y,
                feature_name=["revenue_expense_ratio", "working_capital", "debt_equity_ratio", 
                              "gst_bank_match_score", "legal_flag_count", "sector_risk_flag"]
            )
            params = {
                'objective': 'regression', 
                'verbose': -1, 
                'max_depth': 5,
                'learning_rate': 0.05,
                'min_child_samples': 5
            }
            self.model = lgb.train(params, train_data, num_boost_round=200)
            
            # Save the mock model for future loads
            try:
                os.makedirs(os.path.dirname(path_or_artifact), exist_ok=True)
                self.model.save_model(path_or_artifact)
            except Exception as e:
                print(f"Could not save mock model: {e}")

    def predict(self, features: pd.DataFrame) -> Dict[str, Union[float, str]]:
        """
        Predicts the credit risk.
        Slices to only the 6 model-trained columns before prediction
        so extra enrichment columns never cause a feature-mismatch crash.
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")

        # Keep only the columns the booster was trained on, in training order
        # Add any missing columns as 0 (safe default)
        model_input = features.reindex(columns=MODEL_FEATURES, fill_value=0).astype(float)

        print(f"[model.predict] Input values: {model_input.iloc[0].to_dict()}")

        raw_score = self.model.predict(model_input)[0]

        prob_default = max(0.0, min(1.0, float(raw_score)))
        credit_score = int((1.0 - prob_default) * 100)

        print(f"[model.predict] raw_score={raw_score:.4f}  prob_default={prob_default:.4f}  credit_score={credit_score}")

        if credit_score >= 70:
            decision = "APPROVE"
        elif credit_score >= 50:
            decision = "WATCHLIST"
        else:
            decision = "REJECT"

        return {
            "predicted_score": credit_score / 100.0,
            "decision": decision
        }
