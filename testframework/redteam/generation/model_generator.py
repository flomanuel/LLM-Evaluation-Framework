#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""Structured generation helpers backed by DeepEval models."""

import json
from typing import TypeVar, Any

from deepeval.metrics.utils import initialize_model
from deepeval.models import DeepEvalBaseLLM
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def generate(
        prompt: str,
        response_schema: type[T],
        simulator_model: DeepEvalBaseLLM | str | None,
) -> T:
    """Generate one typed object from a prompt."""
    model, _ = initialize_model(simulator_model)
    return _model_generate(model, prompt, response_schema)


async def a_generate(
        prompt: str,
        response_schema: type[T],
        simulator_model: DeepEvalBaseLLM | str | None,
) -> T:
    """Generate one typed object from a prompt asynchronously."""
    model, _ = initialize_model(simulator_model)
    return await _model_a_generate(model, prompt, response_schema)


def _model_generate(
        model: Any,
        prompt: str,
        response_schema: type[T],
) -> T:
    raw = _call_generate(model, prompt, response_schema)
    return _coerce_response(raw, response_schema)


async def _model_a_generate(
        model: Any,
        prompt: str,
        response_schema: type[T],
) -> T:
    raw = await _call_a_generate(model, prompt, response_schema)
    return _coerce_response(raw, response_schema)


def _call_generate(model: Any, prompt: str, response_schema: type[T]) -> Any:
    generate_fn = getattr(model, "generate", None)
    if generate_fn is None:
        raise RuntimeError("Simulator model does not expose generate().")

    call_patterns = (
        lambda: generate_fn(prompt=prompt, schema=response_schema),
        lambda: generate_fn(prompt, response_schema),
        lambda: generate_fn(prompt=prompt),
        lambda: generate_fn(prompt),
    )
    return _call_with_fallback(call_patterns)


async def _call_a_generate(model: Any, prompt: str, response_schema: type[T]) -> Any:
    a_generate_fn = getattr(model, "a_generate", None)
    if a_generate_fn is None:
        return _call_generate(model, prompt, response_schema)

    call_patterns = (
        lambda: a_generate_fn(prompt=prompt, schema=response_schema),
        lambda: a_generate_fn(prompt, response_schema),
        lambda: a_generate_fn(prompt=prompt),
        lambda: a_generate_fn(prompt),
    )
    result = _call_with_fallback(call_patterns)
    if hasattr(result, "__await__"):
        return await result
    return result


def _call_with_fallback(call_patterns: tuple[Any, ...]) -> Any:
    last_error: TypeError | None = None
    for call in call_patterns:
        try:
            return call()
        except TypeError as exc:
            last_error = exc
            continue
    raise last_error or RuntimeError("Could not call model generation method.")


def _coerce_response(raw: Any, response_schema: type[T]) -> T:
    if isinstance(raw, response_schema):
        return raw

    if isinstance(raw, tuple) and raw:
        if isinstance(raw[0], response_schema):
            return raw[0]
        raw = raw[0]

    if isinstance(raw, dict):
        return response_schema.model_validate(raw)

    if isinstance(raw, BaseModel):
        return response_schema.model_validate(raw.model_dump())

    text = _extract_text(raw)
    as_json = _extract_json(text)
    return response_schema.model_validate(as_json)


def _extract_text(raw: Any) -> str:
    if isinstance(raw, str):
        return raw
    if raw is None:
        return ""
    if hasattr(raw, "text"):
        return str(raw.text)
    if hasattr(raw, "content"):
        return str(raw.content)
    return str(raw)


def _extract_json(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidate = text[first:last + 1]
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("Could not parse JSON object from model output.")
