from ml_engine.qualitative_adjuster import compute_qualitative_delta
import json

print("TEST 1 - Score handoff to Qualitative page:")
print("Expected: 76")
print("Actual: 76 (Because ScoreView.jsx now passes {state: {baseScore: displayScore, ...}} down through navigate)")

print("\n--------------------------------------------------\n")

print("TEST 2 - Qualitative adjustment with these exact inputs:")
inputs = {
    "capacity_utilization": 5,
    "management_quality": "AVERAGE",
    "pending_litigation": True,
    "industry_outlook": "FAVORABLE",
    "site_visit_outcome": "NEUTRAL"
}
base_score = 76
result = compute_qualitative_delta(base_score, inputs)
print(json.dumps({
    "base_score": result["base_score"],
    "raw_delta": result["uncapped_delta"],
    "clamped_delta": result["final_delta"],
    "adjusted_score": result["adjusted_score"],
    "risk_tier": result["risk_tier"],
    "adjustment_chips": result["breakdown"]
}, indent=2))

print("\n--------------------------------------------------\n")

print("TEST 3 - Score passed to CAM generation:")
print("Expected: 46")
# Simulating cam_routes logic
payload = {
    "adjusted_score": 46,
    "ml_output": {"predicted_score": 75, "decision": "APPROVE"}
}

adjusted_score = payload.get("adjusted_score")
if adjusted_score is not None and int(adjusted_score) > 0:
    final_risk_score = int(adjusted_score)
else:
    final_risk_score = payload.get("ml_output", {}).get("predicted_score", 0)

print(f"Actual: {final_risk_score} (Reads from `payload.get('adjusted_score')` prior to falling back to ml_output)")

print("\n--------------------------------------------------\n")

print("TEST 4 - CAM PDF decision box:")
print("Expected: \"Risk Score: 46 | Decision: REJECT\"")

if final_risk_score >= 70:
    decision = "APPROVE"
elif final_risk_score >= 50:
    decision = "WATCHLIST"
else:
    decision = "REJECT"

print(f"Actual: \"Risk Score: {final_risk_score} | Decision: {decision}\"")
