"""
apex/adapters/browsers/dom_recognition.py
Semantic DOM Element Anchor Resolver (matches CSS selectors, ARIA labels, and text landmarks).
"""

class DOMElementRecognizer:
    @staticmethod
    def create_semantic_anchor(tag_name="button", text="", css_selector="", rel_uv=(0.5, 0.5)):
        return {
            "tag": tag_name,
            "text": text,
            "selector": css_selector,
            "relative_uv": list(rel_uv)
        }
