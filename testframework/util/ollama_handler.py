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
        if not OllamaGenerator._has_local_models():
            model_id = os.environ.get("LOCAL_MODEL_ID", False)
            safe_model_id = shlex.quote(model_id)
            os.system(f"ollama run {safe_model_id} >/dev/null 2>&1 &")
            time.sleep(2)

    @staticmethod
    def require_local_model_shutdown() -> None:
        """
        Wait until `ollama ps` no longer lists a model or the user overrides the shutdown requirement.
        """
        # try to stop the local model automatically
        model_id = os.environ.get("LOCAL_MODEL_ID", False)
        if model_id:
            logger.info(f"Stopping local model {model_id}")
            safe_model_id = shlex.quote(model_id)
            os.system(f"ollama stop {safe_model_id} >/dev/null 2>&1")
            time.sleep(2)

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
        running_models = os.popen("ollama ps").read().strip().splitlines()
        return len(running_models) > 1
