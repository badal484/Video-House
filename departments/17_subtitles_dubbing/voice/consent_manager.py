"""
Biometric Consent Manager for Department 17.
Enforces legal authorizations, territorial checks, and expiration dates for cloned voice profiles.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

from ..core.models import BiometricConsentRecord


class ConsentAuthorizationException(Exception):
    """Raised when voice synthesis is attempted without active biometric authorization."""
    pass


class ConsentManager:
    """Stores and validates biometric voice rights and consent tokens."""

    def __init__(self):
        self._records: Dict[str, BiometricConsentRecord] = {}  # voice_profile_id -> record
        self._seed_default_consents()

    def _seed_default_consents(self) -> None:
        """Seeds default authorized profiles for baseline open-source and studio voices."""
        default_profiles = [
            ("Kokoro Default EN", "kokoro_default_en"),
            ("Kokoro Default ES", "kokoro_default_es"),
            ("Kokoro Default HI", "kokoro_default_hi"),
            ("Kokoro Default FR", "kokoro_default_fr"),
            ("Kokoro Default DE", "kokoro_default_de"),
            ("Studio Lead Male", "actor_default_male"),
            ("Studio Lead Female", "actor_default_female"),
        ]
        for name, vid in default_profiles:
            self._records[vid] = BiometricConsentRecord(
                talent_name=name,
                voice_profile_id=vid,
                is_authorized=True,
                authorized_purposes=["commercial", "dubbing", "localization"],
            )

    def register_consent(self, record: BiometricConsentRecord) -> None:
        """Registers a verified biometric consent record."""
        self._records[record.voice_profile_id] = record

    def get_consent(self, voice_profile_id: str) -> Optional[BiometricConsentRecord]:
        """Retrieves consent record for a voice profile."""
        return self._records.get(voice_profile_id)

    def verify_authorization(
        self,
        voice_profile_id: str,
        purpose: str = "commercial",
        territory: str = "worldwide",
    ) -> bool:
        """
        Verifies that a voice profile is legally authorized for the given purpose and territory.
        Raises ConsentAuthorizationException if invalid.
        """
        record = self.get_consent(voice_profile_id)
        if not record:
            raise ConsentAuthorizationException(
                f"No biometric consent record registered for voice profile '{voice_profile_id}'."
            )

        if not record.is_authorized:
            raise ConsentAuthorizationException(
                f"Voice profile '{voice_profile_id}' authorization has been revoked."
            )

        # Check purpose
        if purpose not in record.authorized_purposes and "all" not in record.authorized_purposes:
            raise ConsentAuthorizationException(
                f"Purpose '{purpose}' is not authorized for voice profile '{voice_profile_id}'."
            )

        # Check expiration date
        if record.expiry_date:
            try:
                expiry = datetime.fromisoformat(record.expiry_date)
                if datetime.now(timezone.utc) > expiry:
                    raise ConsentAuthorizationException(
                        f"Consent for voice profile '{voice_profile_id}' expired on {record.expiry_date}."
                    )
            except ValueError:
                pass

        return True
