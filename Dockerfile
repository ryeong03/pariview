FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8080
WORKDIR /app
COPY ai/*.py ./ai/
COPY web/dist/ ./web/dist/
USER 65532:65532
EXPOSE 8080
CMD ["python3", "ai/server.py"]
