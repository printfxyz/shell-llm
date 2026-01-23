# Model-Adaptive Shell Command Generator

This project provides a small, extensible library for building **model-adaptive** system prompts and guardrails for shell command generation. Instead of hard-coding a single system prompt, the generator stores per-model prompt profiles, records feedback, and continually refines the prompt/guardrails that perform best for each target LLM.

## Why this exists

Different LLMs respond better to different system prompts and safety guardrails. This library keeps a lightweight registry that:

- Persists a profile per model (prompt, guardrails, score, feedback history).
- Tracks success/failure feedback and updates prompt quality scores.
- Allows iterating on the system prompt and guardrails without hard-coding a single template.

## Usage

```python
from model_adaptive_shell import ModelAdaptiveShellGenerator

base_prompt = "You are a shell command generator."
base_guardrails = [
    "Avoid destructive commands unless explicitly requested.",
    "Prefer safe, minimal commands.",
]

generator = ModelAdaptiveShellGenerator(
    base_system_prompt=base_prompt,
    base_guardrails=base_guardrails,
)

# Build the best prompt for a target model
prompt_bundle = generator.build_prompt(model_name="gpt-4o")
print(prompt_bundle["system_prompt"])
print(prompt_bundle["guardrails"])

# Record feedback to improve future prompts
feedback = {
    "success": True,
    "notes": "Handled command formatting well.",
}

generator.record_feedback(model_name="gpt-4o", feedback=feedback)
```

## Storage

The registry persists to a JSON file (default: `.model_prompt_registry.json` in the project root). You can provide a custom path if desired.

## Extending

You can extend the prompt refinement logic inside `PromptRegistry.refine_profile` to implement model-specific tuning or A/B testing.
