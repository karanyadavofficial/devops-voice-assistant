FROM python:3.13-slim

# Show print() output immediately in `docker logs`
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Docker CLI, so our Docker tools can talk to the host's Docker
COPY --from=docker:cli /usr/local/bin/docker /usr/local/bin/docker

# Install libraries first (cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then copy our code
COPY main.py tools.py docker_tools.py ./
COPY static ./static

EXPOSE 8000

# Uses the /health endpoint we built in Step 2
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# 0.0.0.0 = listen on all interfaces (required inside a container)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
