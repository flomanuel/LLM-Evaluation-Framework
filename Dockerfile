#Source: https://github.com/guardrails-ai/guardrails-lite-server/blob/main/Dockerfile

# Start our builder image in the multi-stage build
FROM public.ecr.aws/docker/library/python:3.13-slim AS builder

# Accept a build arg for the Guardrails token
# We'll add this to the config using the configure command below
ARG GUARDRAILS_TOKEN

# Set environment variables to avoid writing .pyc files and to unbuffer Python output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# Use a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"


# Copy the requirements file
COPY ./_extras/docker/requirements*.txt .

# Install app dependencies
# If you use Poetry this step might be different
#RUN /opt/venv/bin/pip install -r requirements-lock.txt
RUN /opt/venv/bin/pip install -r requirements.txt


# Run the Guardrails configure command to create a .guardrailsrc file
RUN guardrails configure --enable-metrics --enable-remote-inferencing  --token $GUARDRAILS_TOKEN

# Install validators from Guardrails Hub. Some plugins are flaky on first install.
# Thus, we retry each install a few times.
RUN validators=" \
      hub://tryolabs/restricttotopic \
      hub://guardrails/detect_jailbreak \
      hub://guardrails/toxic_language \
      hub://guardrails/bias_check \
      hub://guardrails/guardrails_pii \
      hub://guardrails/shieldgemma_2b \
      hub://guardrails/llamaguard_7b"; \
    for validator in $validators; do \
      current_attempts=0; \
      max_attempts=4; \
      until [ "$current_attempts" -ge "$max_attempts" ]; do \
        current_attempts=$((current_attempts + 1)); \
        if guardrails hub install "$validator"; then \
          break; \
        fi; \
      done; \
      if [ "$current_attempts" -ge "$max_attempts" ]; then \
        echo "ERROR: Could not install $validator."; \
      fi; \
    done
# Start our final image that we'll use
FROM public.ecr.aws/docker/library/python:3.13-slim

ARG GUARDRAILS_TOKEN

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LOGLEVEL="DEBUG"
ENV GUARDRAILS_LOG_LEVEL="DEBUG"

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

# Run the Guardrails configure command to create a .guardrailsrc file
RUN guardrails configure --disable-metrics --enable-remote-inferencing  --token $GUARDRAILS_TOKEN

# run installs a second time since sometimes, the post install scripts fail to run on the first try
RUN validators=" \
      hub://tryolabs/restricttotopic \
      hub://guardrails/detect_jailbreak \
      hub://guardrails/toxic_language \
      hub://guardrails/bias_check \
      hub://guardrails/guardrails_pii \
      hub://guardrails/shieldgemma_2b \
      hub://guardrails/llamaguard_7b"; \
    for validator in $validators; do \
      current_attempts=0; \
      max_attempts=4; \
      until [ "$current_attempts" -ge "$max_attempts" ]; do \
        current_attempts=$((current_attempts + 1)); \
        if guardrails hub install "$validator"; then \
          break; \
        fi; \
      done; \
      if [ "$current_attempts" -ge "$max_attempts" ]; then \
        echo "ERROR: Could not install $validator."; \
      fi; \
    done

# Copy the config over
COPY ./_extras/docker/config.py ./config.py

EXPOSE 8000

# https://gunicorn.org/asgi/
CMD gunicorn --bind 0.0.0.0:8000 --timeout=90 --workers=1 --worker-class asgi 'guardrails_api.app:create_app(None, "config.py")'
