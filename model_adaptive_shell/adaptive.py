"""Model-adaptive system prompt and guardrail management for shell generators."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_REGISTRY_PATH = Path(".model_prompt_registry.json")


@dataclass
class PromptProfile:
    """Represents the tuned system prompt and guardrails for one model."""

    system_prompt: str
    guardrails: List[str]
    score: float = 0.0
    feedback_history: List[Dict[str, Any]] = field(default_factory=list)
    tuning_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_prompt": self.system_prompt,
            "guardrails": list(self.guardrails),
            "score": self.score,
            "feedback_history": list(self.feedback_history),
            "tuning_notes": list(self.tuning_notes),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptProfile":
        return cls(
            system_prompt=data.get("system_prompt", ""),
            guardrails=list(data.get("guardrails", [])),
            score=float(data.get("score", 0.0)),
            feedback_history=list(data.get("feedback_history", [])),
            tuning_notes=list(data.get("tuning_notes", [])),
        )


class PromptRegistry:
    """Persistent storage for per-model prompt profiles."""

    def __init__(self, path: Path = DEFAULT_REGISTRY_PATH) -> None:
        self.path = path
        self._profiles: Dict[str, PromptProfile] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._profiles = {}
            return
        data = json.loads(self.path.read_text())
        self._profiles = {
            model: PromptProfile.from_dict(profile) for model, profile in data.items()
        }

    def _save(self) -> None:
        payload = {model: profile.to_dict() for model, profile in self._profiles.items()}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    def get_profile(self, model_name: str) -> Optional[PromptProfile]:
        return self._profiles.get(model_name)

    def set_profile(self, model_name: str, profile: PromptProfile) -> None:
        self._profiles[model_name] = profile
        self._save()

    def record_feedback(self, model_name: str, feedback: Dict[str, Any]) -> PromptProfile:
        profile = self._profiles[model_name]
        profile.feedback_history.append(feedback)
        self.refine_profile(profile, feedback)
        self._save()
        return profile

    def refine_profile(self, profile: PromptProfile, feedback: Dict[str, Any]) -> None:
        """Apply lightweight refinement based on feedback.

        This method uses a simple exponential moving average to adjust scores
        while preserving tuning notes that can be leveraged for manual edits.
        """

        success = bool(feedback.get("success"))
        reward = 1.0 if success else -1.0
        profile.score = (profile.score * 0.8) + (reward * 0.2)

        notes = feedback.get("notes")
        if notes:
            profile.tuning_notes.append(str(notes))

        issue = feedback.get("issue")
        if issue and issue not in profile.guardrails:
            profile.guardrails.append(str(issue))


class ModelAdaptiveShellGenerator:
    """Constructs model-specific system prompts with adaptive guardrails."""

    def __init__(
        self,
        base_system_prompt: str,
        base_guardrails: List[str],
        registry_path: Path | None = None,
    ) -> None:
        self.base_system_prompt = base_system_prompt
        self.base_guardrails = base_guardrails
        self.registry = PromptRegistry(registry_path or DEFAULT_REGISTRY_PATH)

    def build_prompt(self, model_name: str) -> Dict[str, Any]:
        profile = self.registry.get_profile(model_name)
        if profile is None:
            profile = PromptProfile(
                system_prompt=self.base_system_prompt,
                guardrails=list(self.base_guardrails),
            )
            self.registry.set_profile(model_name, profile)

        return {
            "model": model_name,
            "system_prompt": profile.system_prompt,
            "guardrails": profile.guardrails,
            "score": profile.score,
            "tuning_notes": profile.tuning_notes,
        }

    def record_feedback(self, model_name: str, feedback: Dict[str, Any]) -> PromptProfile:
        if model_name not in self.registry._profiles:
            self.build_prompt(model_name)
        return self.registry.record_feedback(model_name, feedback)

    def update_prompt(
        self,
        model_name: str,
        system_prompt: Optional[str] = None,
        guardrails: Optional[List[str]] = None,
    ) -> PromptProfile:
        profile = self.registry.get_profile(model_name)
        if profile is None:
            profile = PromptProfile(
                system_prompt=system_prompt or self.base_system_prompt,
                guardrails=guardrails or list(self.base_guardrails),
            )
        else:
            if system_prompt is not None:
                profile.system_prompt = system_prompt
            if guardrails is not None:
                profile.guardrails = guardrails
        self.registry.set_profile(model_name, profile)
        return profile
