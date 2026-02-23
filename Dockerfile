FROM --platform=linux/amd64 python:3.13-slim

RUN pip install uv

ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
ENV PATH="/opt/venv/bin:$PATH"
ENV UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

RUN useradd --create-home appuser && chown -R appuser:appuser /app /opt/venv
USER appuser

EXPOSE 8000

CMD ["adk", "web", "--reload_agents", "--host", "0.0.0.0", "--port", "8000"]
