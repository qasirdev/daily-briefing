"""In-memory user preference store with simple extraction."""

from __future__ import annotations

import re
from uuid import UUID

from backend.schemas.preferences import PreferenceFeedbackRequest, UserPreference

PREFERENCE_PATTERNS: tuple[tuple[str, re.Pattern[str], float], ...] = (
    ("morning_deep_work", re.compile(r"\bmorning\b", re.IGNORECASE), 0.75),
    ("afternoon_meetings", re.compile(r"\bafternoon\b", re.IGNORECASE), 0.7),
    ("shorter_summaries", re.compile(r"\b(shorter|concise|brief)\b", re.IGNORECASE), 0.65),
    ("no_meetings_before_noon", re.compile(r"\bno meetings before\b", re.IGNORECASE), 0.8),
)


def extract_preference(feedback: PreferenceFeedbackRequest) -> UserPreference | None:
    if feedback.original_content.strip() == feedback.edited_content.strip():
        return None

    delta = feedback.edited_content
    for label, pattern, confidence in PREFERENCE_PATTERNS:
        if pattern.search(delta) and not pattern.search(feedback.original_content):
            return UserPreference(
                user_id=feedback.user_id,
                preference_text=f"User prefers: {label.replace('_', ' ')}",
                confidence=confidence,
                source_briefing_id=feedback.briefing_id,
            )

    if len(feedback.edited_content) < len(feedback.original_content) * 0.7:
        return UserPreference(
            user_id=feedback.user_id,
            preference_text="User prefers shorter briefing summaries",
            confidence=0.6,
            source_briefing_id=feedback.briefing_id,
        )
    return None


class PreferenceStore:
    def __init__(self) -> None:
        self._preferences: dict[UUID, UserPreference] = {}

    def add(self, preference: UserPreference) -> UserPreference:
        existing = self._find_conflicting(preference.user_id, preference.preference_text)
        if existing is not None:
            if preference.confidence > existing.confidence:
                updated = existing.model_copy(
                    update={
                        "preference_text": preference.preference_text,
                        "confidence": preference.confidence,
                        "source_briefing_id": preference.source_briefing_id,
                    },
                )
                self._preferences[existing.id] = updated
                return updated
            return existing
        self._preferences[preference.id] = preference
        return preference

    def _find_conflicting(self, user_id: str, text: str) -> UserPreference | None:
        for pref in self._preferences.values():
            if pref.user_id == user_id and pref.preference_text == text:
                return pref
        return None

    def list_for_user(self, user_id: str) -> list[UserPreference]:
        prefs = [p for p in self._preferences.values() if p.user_id == user_id]
        return sorted(prefs, key=lambda item: item.confidence, reverse=True)

    def delete(self, preference_id: UUID) -> bool:
        return self._preferences.pop(preference_id, None) is not None

    def top_context_snippets(self, user_id: str, limit: int = 3) -> list[str]:
        return [pref.preference_text for pref in self.list_for_user(user_id)[:limit]]


preference_store = PreferenceStore()
