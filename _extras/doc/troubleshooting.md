
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
