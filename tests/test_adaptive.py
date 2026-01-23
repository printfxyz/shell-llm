import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from model_adaptive_shell.adaptive import ModelAdaptiveShellGenerator, PromptRegistry


def test_build_prompt_initializes_profile(tmp_path):
    registry_path = tmp_path / "registry.json"
    generator = ModelAdaptiveShellGenerator(
        base_system_prompt="base",
        base_guardrails=["rail-1", "rail-2"],
        registry_path=registry_path,
    )

    bundle = generator.build_prompt("model-a")

    assert bundle["model"] == "model-a"
    assert bundle["system_prompt"] == "base"
    assert bundle["guardrails"] == ["rail-1", "rail-2"]
    assert registry_path.exists()

    data = json.loads(registry_path.read_text())
    assert "model-a" in data


def test_record_feedback_updates_score_and_guardrails(tmp_path):
    registry_path = tmp_path / "registry.json"
    generator = ModelAdaptiveShellGenerator(
        base_system_prompt="base",
        base_guardrails=["rail-1"],
        registry_path=registry_path,
    )
    generator.build_prompt("model-a")

    profile = generator.record_feedback(
        "model-a",
        {"success": True, "notes": "good", "issue": "avoid rm -rf"},
    )

    assert profile.score > 0
    assert "good" in profile.tuning_notes
    assert "avoid rm -rf" in profile.guardrails


def test_update_prompt_overrides_fields(tmp_path):
    registry_path = tmp_path / "registry.json"
    generator = ModelAdaptiveShellGenerator(
        base_system_prompt="base",
        base_guardrails=["rail-1"],
        registry_path=registry_path,
    )
    generator.build_prompt("model-a")

    profile = generator.update_prompt(
        "model-a",
        system_prompt="updated",
        guardrails=["rail-2"],
    )

    assert profile.system_prompt == "updated"
    assert profile.guardrails == ["rail-2"]


def test_registry_loads_existing_profile(tmp_path):
    registry_path = tmp_path / "registry.json"
    generator = ModelAdaptiveShellGenerator(
        base_system_prompt="base",
        base_guardrails=["rail-1"],
        registry_path=registry_path,
    )
    generator.build_prompt("model-a")

    registry = PromptRegistry(registry_path)
    profile = registry.get_profile("model-a")

    assert profile is not None
    assert profile.system_prompt == "base"
