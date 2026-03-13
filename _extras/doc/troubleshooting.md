
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

## Deleting ML models (*NIX)

By default, most ML models can be found under `~/.cache/...`
