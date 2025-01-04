# From https://medium.com/@albertazzir/blazing-fast-python-docker-builds-with-poetry-a78a66f5aed0
FROM python:3.12-bookworm AS builder
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache
WORKDIR /app
RUN pip install poetry==1.8.5
COPY pyproject.toml poetry.lock ./
RUN touch README.md
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-root # --without dev

FROM python:3.12-slim-bookworm AS runtime
WORKDIR /app
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY ./src /app/src
COPY ./conf /app/conf
ENTRYPOINT [ "python", "-m", "src.generate" ]
