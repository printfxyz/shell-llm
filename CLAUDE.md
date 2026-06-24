# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Run the test suite:
```bash
python -m pytest tests/
```

Run a single test:
```bash
python -m pytest tests/test_adaptive.py::test_build_prompt_initializes_profile
```

There is no build step, linter config, or package install file — the library is pure Python with no declared dependencies beyond the standard library.

## Architecture

The library has a single module (`model_adaptive_shell/adaptive.py`) with three layered classes:

**`PromptProfile`** — a dataclass holding the tuned state for one model: `system_prompt`, `guardrails` (list of strings), a float `score`, `feedback_history`, and `tuning_notes`. Serializes to/from JSON via `to_dict` / `from_dict`.

**`PromptRegistry`** — persists a `Dict[model_name → PromptProfile]` to a JSON file (default: `.model_prompt_registry.json` in the working directory). Loads on construction, saves after every mutation. `refine_profile` applies an exponential moving average score update (`score = score*0.8 + reward*0.2`) and appends new guardrails from the `"issue"` field of feedback dicts.

**`ModelAdaptiveShellGenerator`** — the public API. Wraps a `PromptRegistry` and a base prompt/guardrails pair. `build_prompt(model_name)` returns a dict with the current profile (creating a new one from the base if absent). `record_feedback(model_name, feedback)` ensures the profile exists then delegates to the registry. `update_prompt` allows direct overrides of prompt or guardrails for a model.

The registry file is the only persistent state — deleting it resets all learned profiles to the base prompt/guardrails.

## Key Conventions

- `registry_path` can be overridden in tests via `tmp_path` (pytest fixture) to avoid touching the real registry file.
- Feedback dicts support three keys: `"success"` (bool), `"notes"` (string appended to `tuning_notes`), `"issue"` (string added to `guardrails` if not already present).
- `refine_profile` is intentionally simple and is the designated extension point for more sophisticated tuning strategies (e.g., A/B testing, model-specific prompt libraries).
