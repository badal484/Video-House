"""
Glossary Manager for Department 17.
Maintains client-specific terminology, character names, and branded keywords.
Enforces glossary preservation during translation and localization.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional
from uuid import UUID

from ..core.models import GlossaryTerm


class GlossaryManager:
    """Manages project glossaries and validates term preservation in translations."""

    def __init__(self):
        self._glossaries: Dict[str, List[GlossaryTerm]] = {}  # key: f"{project_id}_{target_lang}"

    def register_term(self, project_id: UUID, term: GlossaryTerm) -> None:
        """Registers a glossary term for a project and target language."""
        key = f"{project_id}_{term.target_language.lower()}"
        if key not in self._glossaries:
            self._glossaries[key] = []
        self._glossaries[key].append(term)

    def get_terms(self, project_id: UUID, target_language: str) -> List[GlossaryTerm]:
        """Retrieves all registered glossary terms for a project and language."""
        key = f"{project_id}_{target_language.lower()}"
        return self._glossaries.get(key, [])

    def mask_terms_in_source(self, text: str, project_id: UUID, target_language: str) -> tuple[str, Dict[str, str]]:
        """
        Detects glossary terms in source text and returns masked text with placeholder tokens
        to prevent translation engines from corrupting names or technical terms.
        """
        terms = self.get_terms(project_id, target_language)
        masked_text = text
        token_map: Dict[str, str] = {}

        for idx, term in enumerate(terms):
            flags = 0 if term.case_sensitive else re.IGNORECASE
            pattern = r"\b" + re.escape(term.source_term) + r"\b"
            if re.search(pattern, masked_text, flags):
                token = f"__GLOSSARY_TOKEN_{idx}__"
                masked_text = re.sub(pattern, token, masked_text, flags=flags)
                token_map[token] = term.target_term

        return masked_text, token_map

    def unmask_terms(self, text: str, token_map: Dict[str, str]) -> str:
        """Restores mandatory target glossary terms from placeholders."""
        result = text
        for token, target_term in token_map.items():
            result = result.replace(token, target_term)
        return result

    def verify_preservation(
        self,
        target_text: str,
        project_id: UUID,
        target_language: str,
    ) -> List[str]:
        """
        Verifies which required target terms are present in the localized translation.
        Returns a list of preserved terms.
        """
        terms = self.get_terms(project_id, target_language)
        preserved: List[str] = []
        for term in terms:
            flags = 0 if term.case_sensitive else re.IGNORECASE
            pattern = re.escape(term.target_term)
            if re.search(pattern, target_text, flags):
                preserved.append(term.target_term)
        return preserved
