FROM python:3.13-slim AS base

LABEL org.opencontainers.image.title="DRAFT Protocol"
LABEL org.opencontainers.image.description="Intake governance for AI tool calls"
LABEL org.opencontainers.image.source="https://github.com/georgegoytia/draft-protocol"
LABEL org.opencontainers.image.licenses="Apache-2.0"

WORKDIR /app

# Install only production dependencies
COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir . && \
    rm -rf /root/.cache

# Non-root user
RUN useradd --create-home draft
USER draft

# Default to SSE transport for containerized use
ENV DRAFT_TRANSPORT=sse
ENV DRAFT_HOST=0.0.0.0
ENV DRAFT_PORT=8420
ENV DRAFT_DB_PATH=/home/draft/.draft_protocol/draft.db

EXPOSE 8420

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8420/sse')" || exit 1

ENTRYPOINT ["python", "-m", "draft_protocol"]
CMD ["--transport", "sse", "--host", "0.0.0.0", "--port", "8420"]
