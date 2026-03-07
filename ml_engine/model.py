"""
ML Engine - Scoring models (LightGBM).
"""

import os
import numpy as np
import pandas as pd
import lightgbm as lgb
from typing import Dict, Union

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
            print(f"Model not found at {path_or_artifact}. Initializing untrained mock booster.")
            # Dummy training data to fit LightGBM schema
            train_data = lgb.Dataset(
                data=np.array([
                    [1.2, 200000, 0.5, 0.9, 0, 0], 
                    [0.8, -50000, 2.0, 0.4, 3, 1]
                ]),
                label=[0.1, 0.9], # 0.1 = Approve (Low risk), 0.9 = Reject (High risk)
                feature_name=["revenue_expense_ratio", "working_capital", "debt_equity_ratio", 
                              "gst_bank_match_score", "legal_flag_count", "sector_risk_flag"]
            )
            params = {'objective': 'regression', 'verbose': -1, 'min_data_in_leaf': 1}
            self.model = lgb.train(params, train_data, num_boost_round=10)
            
            # Save the mock model for future loads
            try:
                os.makedirs(os.path.dirname(path_or_artifact), exist_ok=True)
                self.model.save_model(path_or_artifact)
            except Exception as e:
                print(f"Could not save mock model: {e}")

    def predict(self, features: pd.DataFrame) -> Dict[str, Union[float, str]]:
        """
        Predicts the credit risk.
        Returns mapped classification based on thresholds.
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
            
        # Predict returns an array, take the first value
        raw_score = self.model.predict(features)[0]
        
        # Scale score to strictly 0.0 - 1.0 bounds (or 0-100)
        # Assuming the model outputs probability of DEFAULT. 
        # Convert it to a traditional credit score out of 100.
        prob_default = max(0.0, min(1.0, float(raw_score)))
        credit_score = int((1.0 - prob_default) * 100)
        
        # User defined thresholds (APPROVE >= 70, WATCHLIST 50-69, REJECT < 50)
        if credit_score >= 70:
            decision = "APPROVE"
        elif credit_score >= 50:
            decision = "WATCHLIST"
        else:
            decision = "REJECT"
            
        return {
            "predicted_score": credit_score / 100.0, # Keep float response stable for APIs if needed, though int is clearer
            "decision": decision
        }
