#!/bin/bash

#
# Copyright (c) 2026.
# Florian Emanuel Sauer
#

# https://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    -e|--all-extras)
      EXTRAS="$1"
      shift
      ;;
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
    *)
      POSITIONAL_ARGS+=("$1")
      shift
      ;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

install_guardrails_models() {
  ./.venv/bin/guardrails hub install hub://guardrails/sensitive_topics
  ./.venv/bin/guardrails hub install hub://guardrails/detect_jailbreak
  ./.venv/bin/guardrails hub install hub://guardrails/toxic_language
  ./.venv/bin/guardrails hub install hub://guardrails/bias_check
  ./.venv/bin/guardrails hub install hub://guardrails/guardrails_pii
  ./.venv/bin/guardrails hub install hub://guardrails/shieldgemma_2b
  ./.venv/bin/guardrails hub install hub://guardrails/llamaguard_7b
}

if [[ -n "${EXTRAS}" ]]; then
  echo "Installing all dependencies, including Guardrails AI models..."
  # reinstall is needed since Guardrails AI installer messes with the dependencies
  uv sync --all-extras --reinstall
  guardrails configure
  install_guardrails_models
else
  echo "Installing production dependencies..."
  # reinstall is needed since Guardrails AI installer messes with the dependencies
  uv sync --reinstall
  guardrails configure
  install_guardrails_models
fi

