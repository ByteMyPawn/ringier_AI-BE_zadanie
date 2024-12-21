FROM python:3.11-slim

WORKDIR /app

# Nainštaluj Poetry
RUN pip install poetry

# Skopíruj všetky súbory do kontajnera
COPY . /app

# Nainštaluj závislosti pomocou Poetry
RUN poetry install --no-dev --no-interaction --no-ansi

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0"]
