FROM python:3.12.1-alpine3.19 as build

RUN apk add gcc musl-dev
RUN pip install --upgrade pip && \
    pip install poetry==1.7.1

WORKDIR /build
COPY poetry.lock pyproject.toml /build
RUN poetry config virtualenvs.in-project true && \
    poetry install --only main --no-root --no-interaction


FROM python:3.12.1-alpine3.19
COPY --from=build /build/.venv /build/.venv

ENV PATH=/build/.venv/bin:$PATH
ENV PYTHONPATH=$PYTHONPATH:/opt
COPY moneyctl /opt/moneyctl
RUN ln -s /opt/moneyctl/__main__.py /usr/local/bin/moneyctl

ENTRYPOINT ["/usr/local/bin/moneyctl"]
