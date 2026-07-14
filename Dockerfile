FROM python:3.14-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
RUN apt-get install proton-vpn-cli

COPY --from=docker.io/astral/uv:latest /uv /bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY main.py .

CMD ["uv", "run", "main.py"]