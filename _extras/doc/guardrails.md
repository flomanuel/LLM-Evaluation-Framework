# Guardrails AI

## Remote Inference

Create an account and API-key under https://guardrailsai.com/.

Important: do opt in to remote inferencing. This will send all guardrails to the guardrails.ai server. But be aware of
the "100 rq / 1m" and "500 rq / 5m" limit.

```bash
uv sync
guardrails configure
```

The following validators are used. Gemma and LlamaGuard are remote inference only.

```bash
  guardrails hub install hub://guardrails/sensitive_topics
  guardrails hub install hub://guardrails/detect_jailbreak
  guardrails hub install hub://guardrails/toxic_language
  guardrails hub install hub://guardrails/bias_check
  guardrails hub install hub://guardrails/guardrails_pii
  guardrails hub install hub://guardrails/shieldgemma_2b
  guardrails hub install hub://guardrails/llamaguard_7b
```

# LlamaFirewall

## Setup Hugging Face

Install the [Hugging Face CLI](https://huggingface.co/docs/huggingface_hub/guides/cli).

Authenticate with the Hugging Face CLI via an existing / new token.

Set hugging face cache home dir in env file (HF_HOME).

Generate an API key for TogetherAI and set it in the .env file (TOGETHER_API_KEY).

## Generate TogetherAI API key

Visit the [dashboard](https://api.together.ai) to generate an API key.

## Request Access to Prompt Guard

Visit the [Hugging Face model page](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M/tree/main) to request
access to Prompt Guard.

# Lakera Guard

## Access

First, create a free account from the [Lakera Guard website](https://www.lakera.ai/).

Then create a new API key from the [API Keys page](https://platform.lakera.ai/account/api-keys) and paste it into the
.env file (`LAKERA_GUARD_API_KEY`).

Also set `LAKERA_GUARD_PROJECT_ID` in `.env`. The Lakera guard integration requires this value.

## Project ID

Set up a project, store the project ID and paste it into the .env file (LAKERA_GUARD_PROJECT_ID).

# Google Model Armor

Install the [Google Cloud CLI](https://docs.cloud.google.com/sdk/docs/install-sdk).
Authenticate with the Google Cloud CLI: `gcloud auth login`.
Set up a project and acticate it on the Google Cloud CLI: `gcloud config set project [PROJECT_ID]`.

Create a new template under "Security" → "Model Armor"

A suggested default template config can be found under `_extras/gcp/*`.

Set vales for the GCP Model Armor in the `.env` file.

Set up Application Default Credentials (ADC):
see [here](https://docs.cloud.google.com/docs/authentication/provide-credentials-adc#how-to).

For local development environments, use `gcloud auth application-default login` to set up ADC.

# Troubleshooting

## Guardrails AI

### Docker

Guardrails AI can be run using the provided Dockerfile since on ARM macOS, running it on the host crashes due to mixed
usage of tensorflow and pytorch.

Sometimes, the image needs to be build twice because the internal dependency resolver used by Guardrails AI misses some
dependencies.

```bash
docker-compose build --no-cache
# and
docker compose up
```

### CLI command `guardrails` fails

If the cli command `guardrails` is not available, try runinng `source ./.venv/bin/activate`, even if you've already
activated the venv.

### filter can't be found when installing from the hub

The same may apply for other guardrails-related error, e.g. if one filter can't be found when installing it from the
hub.

### Deleting an ML model

From the code:

```python
MODEL_CACHE_DIR = os.environ.get(
    "GUARDRAILS_MODEL_CACHE_PATH_OVERRIDE",
    Path.home() / ".cache" / "guardrails_cache"
)
```