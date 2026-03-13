# Details on setting up the Guardrails

## Guardrails AI

### Remote Inference

Create an account and API key from the [admin interface](https://guardrailsai.com/).

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

## LlamaFirewall

### Setting up Hugging Face

Install the [Hugging Face CLI](https://huggingface.co/docs/huggingface_hub/guides/cli).

Authenticate with the Hugging Face CLI via an existing / new token.

Set hugging face cache home dir in env file (HF_HOME).

Generate an API key for TogetherAI and set it in the .env file (TOGETHER_API_KEY).

### Generate TogetherAI API key

Visit the [dashboard](https://api.together.ai) to generate an API key.

### Request Access to Prompt Guard

Visit the [Hugging Face model page](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M/tree/main) to request
access to Prompt Guard.

## Lakera Guard

### Access

First, create a free account from the [Lakera Guard website](https://www.lakera.ai/).

Then create a new API key from the [API Keys page](https://platform.lakera.ai/account/api-keys) and paste it into the
.env file (`LAKERA_GUARD_API_KEY`).

Also set `LAKERA_GUARD_PROJECT_ID` in `.env`. The Lakera guard integration requires this value.

### Project ID

Set up a project, store the project ID and paste it into the .env file (LAKERA_GUARD_PROJECT_ID).

## Google Model Armor

Install the [Google Cloud CLI](https://docs.cloud.google.com/sdk/docs/install-sdk).
Authenticate with the Google Cloud CLI: `gcloud auth login`.
Set up a project and acticate it on the Google Cloud CLI: `gcloud config set project [PROJECT_ID]`.

Create a new template under "Security" → "Model Armor"

A suggested default template config can be found under `_extras/gcp/*`.

Set vales for the GCP Model Armor in the `.env` file.

Set up Application Default Credentials (ADC):
see the [GCP docs](https://docs.cloud.google.com/docs/authentication/provide-credentials-adc#how-to) for details.

For local development environments, use `gcloud auth application-default login` to set up ADC.

## LLM Guard

For LLM Guard, everything should work out of the box.
