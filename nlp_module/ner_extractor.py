"""
Named Entity Recognition using spaCy + regex only.
HuggingFace bert-base-NER removed — it caused OOM crashes on Railway by
downloading a 400MB model at runtime on top of the already-loaded
sentence-transformers model.
spaCy (en_core_web_sm) is pre-installed via nixpacks.toml and covers
ORG / PERSON / LOC / MONEY / DATE. Regex handles PAN / CIN / GSTIN.
"""
import re
import spacy
from typing import List, Dict

# Regex Patterns for Indian financial identifiers
PAN_REGEX   = r"[A-Z]{5}[0-9]{4}[A-Z]"
CIN_REGEX   = r"L\d{6}[A-Z]{2}\d{4}[A-Z]{3}\d{6}"
GSTIN_REGEX = r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}"


class NERExtractor:
    def __init__(self):
        # Load spaCy model (installed at build time via nixpacks.toml)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
            self.nlp = spacy.load("en_core_web_sm")

        # Add custom rules for Indian financial red-flags
        if "entity_ruler" not in self.nlp.pipe_names:
            ruler = self.nlp.add_pipe("entity_ruler", before="ner")
            ruler.add_patterns([
                {"label": "LAW", "pattern": [{"lower": "insolvency"}, {"lower": "act"}]},
                {"label": "LAW", "pattern": [{"lower": "npa"}]},
                {"label": "LAW", "pattern": [{"lower": "default"}]},
            ])

        print("[NERExtractor] spaCy model loaded successfully.")

    def extract_regex_entities(self, text: str) -> List[Dict]:
        entities = []
        for match in re.finditer(PAN_REGEX, text):
            entities.append({"type": "PAN",   "text": match.group()})
        for match in re.finditer(CIN_REGEX, text):
            entities.append({"type": "CIN",   "text": match.group()})
        for match in re.finditer(GSTIN_REGEX, text):
            entities.append({"type": "GSTIN", "text": match.group()})
        return entities

    def extract_spacy_entities(self, text: str) -> List[Dict]:
        try:
            # Limit input to 5000 chars so spaCy doesn't time out on huge docs
            doc = self.nlp(text[:5000])
            entities = []
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PERSON", "MONEY", "DATE", "LAW", "GPE", "LOC"]:
                    entities.append({"type": ent.label_, "text": ent.text})
            return entities
        except Exception as e:
            print(f"[NERExtractor] spaCy extraction failed: {e}")
            return []

    def extract_entities(self, text: str) -> List[Dict]:
        regex_ents = self.extract_regex_entities(text)
        spacy_ents = self.extract_spacy_entities(text)

        all_ents = regex_ents + spacy_ents

        # Deduplicate
        unique_ents, seen = [], set()
        for ent in all_ents:
            key = f"{ent['type']}_{ent['text']}"
            if key not in seen:
                seen.add(key)
                unique_ents.append(ent)

        return unique_ents


# ── Singleton: loaded ONCE at startup, reused on every request ──
_ner_instance: NERExtractor = None


def _get_extractor() -> NERExtractor:
    global _ner_instance
    if _ner_instance is None:
        print("[ner_extractor] Loading NER singleton (spaCy only)...")
        _ner_instance = NERExtractor()
        print("[ner_extractor] NER singleton ready.")
    return _ner_instance


def extract_entities(text: str) -> List[Dict]:
    """
    Public API.
    Returns: [{"type": "ORG", "text": "Orbit Holdings Ltd."}, ...]
    """
    return _get_extractor().extract_entities(text)
