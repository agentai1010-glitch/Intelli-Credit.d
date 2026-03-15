"""
Prompt and generate CAM draft using LLM.
"""
import os
import json
from typing import Dict, Any

def generate_summaries(input_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Uses an LLM to automatically fill sections with fluent narrative summaries.
    Returns a dictionary of generated summary texts.
    """
    # Extract data for context
    features = input_data.get("features", {})
    entity_data = input_data.get("entity_data", [])
    research = input_data.get("research", [])
    ml_output = input_data.get("ml_output", {})
    
    # Check for OpenAI API Key
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key and api_key != "your_openai_api_key":
        try:
            from openai import OpenAI
            # Route to OpenRouter if key is an OpenRouter key
            if api_key.startswith("sk-or-"):
                client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
            else:
                client = OpenAI(api_key=api_key)
            
            prompt = f"""
            You are a senior credit analyst writing a Credit Appraisal Memo (CAM).
            Based on the following data, write concise, professional summaries for:
            1. Character Risk (management history, legal flags, news history).
            2. Conditions Summary (external risks, sector trends, overall news).
            3. Final Recommendation (Approve/Watchlist/Reject with a 1-sentence rationale).
            
            Context:
            - Features: {json.dumps(features)}
            - ML Score/Decision: {json.dumps(ml_output)}
            - NLP Flags: {json.dumps(entity_data)}
            - Web Research: {json.dumps(research)}
            
            Return ONLY a valid JSON object with keys: 'character_summary', 'conditions_summary', 'recommendation'.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result_str = response.choices[0].message.content.strip()
            # Try to parse the json
            if result_str.startswith("```json"):
                result_str = result_str[7:-3]
            return json.loads(result_str)
            
        except Exception as e:
            print(f"Failed to use OpenAI API: {e}. Falling back to rule-based mock summaries.")
            
    # Fallback to rule-based / mock summarization if no API or error
    decision = ml_output.get("decision", "Watchlist")
    
    # Character summary based on NLP flags
    law_flags = [e.get("text") for e in entity_data if e.get("type") == "LAW"]
    if law_flags:
        char_summary = f"The promoter is associated with adverse legal records related to: {', '.join(law_flags)}. High risk."
    else:
        char_summary = "The promoter has no adverse news history in the past 6 months. Management profile appears stable."
        
    # Conditions summary based on research
    if research:
        # Check research tags
        all_tags = []
        for r in research:
            all_tags.extend(r.get("tags", []))
        if all_tags:
            cond_summary = f"External risk signals detected: {', '.join(set(all_tags))}. Sectoral headwinds may affect performance."
        else:
            cond_summary = "No major derogatory external news found. Sector trend appears neutral."
    else:
        cond_summary = "No external news or risk circulars detected during web research."
        
    # Recommendation logic
    if decision == "Reject":
        rec = f"Reject due to ML Model flagged risks and adverse legal/compliance signals."
    elif decision == "Watchlist":
        rec = f"Classified as 'Watchlist'. Require additional collateral or quarterly reviews due to moderate risk indicators."
    else:
        rec = f"Approve request. Financials and background checks are clear."

    return {
        "character_summary": char_summary,
        "conditions_summary": cond_summary,
        "recommendation": rec
    }
