# Stage 1: package the Chrome extension (the zip is a build output, not a tracked file)
FROM python:3.13-slim AS extension
WORKDIR /src
COPY LICENSE ./
COPY extension/ ./extension/
RUN mkdir -p web/dist && python3 extension/package.py

# Stage 2: runtime (stdlib-only Python server + static web app)
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8080
WORKDIR /app
COPY ai/*.py ./ai/
COPY web/dist/ ./web/dist/
COPY --from=extension /src/web/dist/pariview-extension.zip ./web/dist/pariview-extension.zip
USER 65532:65532
EXPOSE 8080
CMD ["python3", "ai/server.py"]
