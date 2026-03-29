# Official Python 3.13 slim to reduce attack surface and size
FROM python:3.13-slim

# Inject `uv` directly into the container from the official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1 

# Create a non-root user
RUN adduser --disabled-password --gecos '' api_user

WORKDIR /app

# Hand over folder ownership to our non-root user
RUN chown -R api_user:api_user /app

# Switch from 'root' to 'api_user'
USER api_user

# Copy ONLY the dependency files first
COPY --chown=api_user:api_user pyproject.toml uv.lock ./

# Install dependencies using the lockfile (without installing the app code yet)
RUN uv sync --frozen --no-dev --no-install-project

# Copy the actual application code
COPY --chown=api_user:api_user ./app ./app

# Sync again to ensure the project itself is linked into the virtual environment
RUN uv sync --frozen --no-dev

# Expose the port Uvicorn will listen on
EXPOSE 8000

# Put the uv virtual environment at the front of the PATH
# This ensures that when called `uvicorn`, it uses the one inside the .venv
ENV PATH="/app/.venv/bin:$PATH"

# The command that starts the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
