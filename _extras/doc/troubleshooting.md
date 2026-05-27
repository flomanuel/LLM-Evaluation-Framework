# Troubleshooting

## Guardrails AI

### Docker

Guardrails AI is built from `Dockerfile.guardrails` and runs as the `guardrails_ai` compose service.
On ARM macOS, running Guardrails AI directly on the host crashes due to mixed tensorflow/pytorch usage —
use the container instead.

Sometimes the image needs to be built twice because the internal Guardrails AI dependency resolver
misses some packages on the first pass:

```bash
docker compose build --no-cache guardrails_ai
docker compose up -d
```

### CLI command `guardrails` fails

If the `guardrails` CLI is not available after activating the venv, try sourcing the activation
script explicitly:

```bash
source ./.venv/bin/activate
```

## Testframework container

### Image does not reflect local source changes

The `testframework` image copies source at build time. After editing `testframework/`, rebuild:

```bash
docker compose build testframework
```

### Container cannot reach Ollama on the host

The container uses `host.docker.internal` to reach the host-side Ollama daemon. On Linux this
requires the `extra_hosts: host.docker.internal:host-gateway` entry (already set in
`docker-compose.yml`). Verify Ollama is listening:

```bash
curl http://localhost:11434/api/tags
```

If you run Ollama on a non-default port or address, set `OLLAMA_HOST` in your `.env`:

```
OLLAMA_HOST=http://host.docker.internal:<port>
```

### HuggingFace models re-downloaded on every run

The host cache is mounted at `~/.cache/huggingface`. If the mount is missing or the path does not
exist the container falls back to downloading models fresh each run. Ensure the directory exists:

```bash
mkdir -p ~/.cache/huggingface
```

## Deleting ML models (*NIX)

By default, most ML models can be found under `~/.cache/...`
