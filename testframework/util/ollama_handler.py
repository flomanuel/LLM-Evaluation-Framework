#  Copyright (c) 2026.
#  Florian Emanuel Sauer
import os
import shlex
import time

from deepeval.models import OllamaModel
from loguru import logger


class OllamaGenerator:
    """Handle the local Ollama model needed for generating attacks and techniques."""

    _ollama_inference_request_timeout = 150
    _chatbot: OllamaModel | None = None

    @staticmethod
    def get_chatbot() -> OllamaModel:
        model_id = os.environ.get("LOCAL_MODEL_ID", False)
        if OllamaGenerator._chatbot is None and model_id is not False:
            OllamaGenerator._chatbot = OllamaModel(
                model=model_id,
                # https://huggingface.co/mlabonne/gemma-3-27b-it-abliterated-GGUF
                generation_kwargs={"top_p": 0.95, "top_k": 64},
                temperature=1.0,
                timeout=OllamaGenerator._ollama_inference_request_timeout,
            )
        return OllamaGenerator._chatbot

    @staticmethod
    def start_model_if_not_running():
        if not OllamaGenerator._has_local_models():
            model_id = os.environ.get("LOCAL_MODEL_ID", False)
            safe_model_id = shlex.quote(model_id)
            os.system(f"ollama run {safe_model_id} >/dev/null 2>&1 &")
            time.sleep(5)

    @staticmethod
    def require_local_model_shutdown() -> None:
        """Wait until `ollama ps` no longer lists a model or the user overrides."""
        while True:
            user_choice = input(
                "🔨 Please shut down the local model 🔨"
                "Then press Enter to continue, or type 'override' to proceed."
            ).strip().lower()

            if user_choice == "override":
                logger.warning(
                    "Proceeding with cooldown, even though `ollama ps` might still list a model."
                )
                return

            if not OllamaGenerator._has_local_models():
                logger.info("No local model could be found. Starting retry cooldown.")
                return

            logger.warning(
                "`ollama ps` still lists running models; can't start the cooldown."
            )

    @staticmethod
    def _has_local_models() -> bool:
        """Return whether `ollama ps` currently lists at least one running model."""
        running_models = os.popen("ollama ps").read().strip().splitlines()
        return len(running_models) > 1
