#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


import os
import shlex
import time

from deepeval.models import OllamaModel
from loguru import logger


class OllamaGenerator:
    """Handle the local Ollama model needed for generating attacks and techniques."""

    _default_ollama_inference_request_timeout_seconds = 240.0
    _startup_wait_seconds = 2
    _shutdown_wait_seconds = 2
    _chatbot: OllamaModel | None = None

    @staticmethod
    def get_chatbot() -> OllamaModel:
        """
        Get the local Ollama model.
        """
        model_id = os.environ.get("LOCAL_MODEL_ID", False)
        if OllamaGenerator._chatbot is None and model_id is not False:
            timeout = OllamaGenerator._get_timeout()
            OllamaGenerator._chatbot = OllamaModel(
                model=model_id,
                # https://huggingface.co/mlabonne/gemma-3-27b-it-abliterated-GGUF
                generation_kwargs={"top_p": 0.95, "top_k": 64},
                temperature=1.0,
                # https://github.com/ollama/ollama-python/blob/main/ollama/_client.py#L86
                # https://github.com/confident-ai/deepeval/blob/main/deepeval/models/llms/ollama_model.py#L229
                timeout=timeout,
            )
        return OllamaGenerator._chatbot

    @staticmethod
    def _get_timeout() -> float:
        """Read the timeout from DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE."""
        timeout_raw = os.environ.get(
            "DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", ""
        ).strip()
        if timeout_raw == "":
            return OllamaGenerator._default_ollama_inference_request_timeout_seconds
        try:
            timeout = float(timeout_raw)
            if timeout <= 0:
                raise ValueError
            return timeout
        except ValueError:
            logger.warning("Timeout configured for DeepEval / DeepTeam is no number")
            return OllamaGenerator._default_ollama_inference_request_timeout_seconds

    @staticmethod
    def start_model_if_not_running():
        """
        Start the local Ollama model if it is not already running.
        """
        model_id = os.environ.get("LOCAL_MODEL_ID", False)
        OllamaGenerator.start_model_by_name_if_not_running(model_id)

    @staticmethod
    def start_model_by_name_if_not_running(model_id: str | bool | None) -> None:
        """Start a specific Ollama model if it is not already running."""
        if not model_id:
            logger.warning("Cannot start Ollama model because no model id was provided")
            return

        if OllamaGenerator._is_model_running(str(model_id)):
            return

        safe_model_id = shlex.quote(str(model_id))
        os.system(f"ollama run {safe_model_id} >/dev/null 2>&1 &")
        time.sleep(OllamaGenerator._startup_wait_seconds)

    @staticmethod
    def require_local_model_shutdown() -> None:
        """
        Wait until `ollama ps` no longer lists a model or the user overrides the shutdown requirement.
        """
        # try to stop the local model automatically
        model_id = os.environ.get("LOCAL_MODEL_ID", False)
        OllamaGenerator.stop_model_by_name(model_id)

        # check if the model is running
        if OllamaGenerator._has_local_models():
            # require manual shutdown
            while True:
                user_choice = input(
                    "🔨 Please shut down the local model 🔨\n"
                    "Then press Enter to continue, or type 'override' to proceed"
                ).strip().lower()

                if user_choice == "override":
                    logger.warning(
                        "Proceeding with cooldown, even though `ollama ps` might still list a model"
                    )
                    return

                if not OllamaGenerator._has_local_models():
                    logger.info("No local model could be found. Starting cooldown")
                    return

                logger.warning(
                    "`ollama ps` still lists running models; can't start the cooldown"
                )

    @staticmethod
    def _has_local_models() -> bool:
        """
        Return whether `ollama ps` currently lists at least one running model.
        """
        return bool(OllamaGenerator._list_running_models())

    @staticmethod
    def stop_model_by_name(model_id: str | bool | None) -> None:
        """Stop a specific Ollama model if a model id was provided."""
        if not model_id:
            return

        logger.info(f"Stopping local model {model_id}")
        safe_model_id = shlex.quote(str(model_id))
        os.system(f"ollama stop {safe_model_id} >/dev/null 2>&1")
        time.sleep(OllamaGenerator._shutdown_wait_seconds)

    @staticmethod
    def _is_model_running(model_id: str) -> bool:
        """Return whether the given model is currently listed by `ollama ps`."""
        return model_id in OllamaGenerator._list_running_models()

    @staticmethod
    def _list_running_models() -> list[str]:
        """Return all running model names listed by `ollama ps`."""
        running_models = os.popen("ollama ps").read().strip().splitlines()
        if len(running_models) <= 1:
            return []

        models: list[str] = []
        for line in running_models[1:]:
            parts = line.split()
            if parts:
                models.append(parts[0])
        return models
