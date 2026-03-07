"""
Named Entity Recognition using spaCy and Transformers.
Models are loaded ONCE as a module-level singleton to avoid OOM crashes on Railway.
"""
import re
import spacy
from transformers import pipeline
from typing import List, Dict

# Regex Patterns
PAN_REGEX = r"[A-Z]{5}[0-9]{4}[A-Z]"
CIN_REGEX = r"L\d{6}[A-Z]{2}\d{4}[A-Z]{3}\d{6}"
GSTIN_REGEX = r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}"


class NERExtractor:
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
            self.nlp = spacy.load("en_core_web_sm")

        # Add custom rule for LAW
        if "entity_ruler" not in self.nlp.pipe_names:
            ruler = self.nlp.add_pipe("entity_ruler", before="ner")
            patterns = [
                {"label": "LAW", "pattern": [{"lower": "insolvency"}, {"lower": "act"}]},
                {"label": "LAW", "pattern": [{"lower": "npa"}]}
            ]
            ruler.add_patterns(patterns)

        # Load HuggingFace NER pipeline — wrapped so failure doesn't crash startup
        try:
            self.hf_ner = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple",
                truncation=True,
                max_length=512
            )
            print("[NERExtractor] HuggingFace NER loaded successfully.")
        except Exception as e:
            print(f"[NERExtractor] HuggingFace NER failed to load: {e}. Falling back to spaCy only.")
            self.hf_ner = None

    def extract_regex_entities(self, text: str) -> List[Dict]:
        entities = []
        for match in re.finditer(PAN_REGEX, text):
            entities.append({"type": "PAN", "text": match.group()})
        for match in re.finditer(CIN_REGEX, text):
            entities.append({"type": "CIN", "text": match.group()})
        for match in re.finditer(GSTIN_REGEX, text):
            entities.append({"type": "GSTIN", "text": match.group()})
        return entities

    def extract_spacy_entities(self, text: str) -> List[Dict]:
        try:
            doc = self.nlp(text[:5000])  # Limit input size for spaCy
            entities = []
            for ent in doc.ents:
                if ent.label_ in ["MONEY", "DATE", "LAW", "GPE", "LOC"]:
                    entities.append({"type": ent.label_, "text": ent.text})
            return entities
        except Exception as e:
            print(f"[NERExtractor] spaCy extraction failed: {e}")
            return []

    def extract_hf_entities(self, text: str) -> List[Dict]:
        if self.hf_ner is None:
            return []
        try:
            # Truncate to first 1000 chars to stay safely within BERT 512-token limit
            hf_results = self.hf_ner(text[:1000])
            entities = []
            for res in hf_results:
                ent_type = res.get("entity_group", "")
                if ent_type in ["ORG", "PER", "LOC"]:
                    mapped_type = "PERSON" if ent_type == "PER" else ent_type
                    entities.append({"type": mapped_type, "text": res.get("word", "")})
            return entities
        except Exception as e:
            print(f"[NERExtractor] HF NER extraction failed: {e}")
            return []

    def extract_entities(self, text: str) -> List[Dict]:
        regex_ents = self.extract_regex_entities(text)
        spacy_ents = self.extract_spacy_entities(text)
        hf_ents = self.extract_hf_entities(text)

        all_ents = regex_ents + spacy_ents + hf_ents

        # Deduplicate (simple exact-match)
        unique_ents = []
        seen = set()
        for ent in all_ents:
            identifier = f"{ent['type']}_{ent['text']}"
            if identifier not in seen:
                seen.add(identifier)
                unique_ents.append(ent)

        return unique_ents


# ── Singleton: loaded ONCE at startup, reused on every request ──
_ner_instance: NERExtractor = None


def _get_extractor() -> NERExtractor:
    global _ner_instance
    if _ner_instance is None:
        print("[ner_extractor] Initialising NER singleton...")
        _ner_instance = NERExtractor()
        print("[ner_extractor] NER singleton ready.")
    return _ner_instance


def extract_entities(text: str) -> List[Dict]:
    """
    Public API — returns list of dicts like {"type": "ORG", "text": "Orbit Holdings"}
    Models are loaded on first call and reused for all subsequent calls.
    """
    return _get_extractor().extract_entities(text)
