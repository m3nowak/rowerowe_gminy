FROM docker.io/library/almalinux:9-minimal AS base
LABEL org.opencontainers.image.source="https://github.com/m3nowak/rowerowe_gminy"
LABEL org.opencontainers.image.description="Rowerowe Gminy"
LABEL org.opencontainers.image.licenses=Apache-2.0

FROM base AS common
RUN ["microdnf", "install", "-y", "python3.12", "python3.12-pip"]

FROM common AS build
RUN ["python3.12", "-m", "pip", "install", "pdm"]
COPY . /app
WORKDIR /app
RUN ["pdm", "build"]
RUN pdm export --prod --no-hashes --no-extras -o constraints.txt

FROM common as venv-all
RUN ["python3.12", "-m", "venv", "/home/rgapp/venv"]
COPY --from=build /app/dist/*.whl /app/whl/
COPY --from=build /app/constraints.txt /app/constraints.txt
RUN /home/rgapp/venv/bin/pip install -f /app/whl -c /app/constraints.txt rowerowe_gminy[all]

FROM common as venv-api
RUN ["python3.12", "-m", "venv", "/home/rgapp/venv"]
COPY --from=build /app/dist/*.whl /app/whl/
COPY --from=build /app/constraints.txt /app/constraints.txt
RUN /home/rgapp/venv/bin/pip install -f /app/whl -c /app/constraints.txt rowerowe_gminy[api]

FROM common as venv-db
RUN ["python3.12", "-m", "venv", "/home/rgapp/venv"]
COPY --from=build /app/dist/*.whl /app/whl/
COPY --from=build /app/constraints.txt /app/constraints.txt
RUN /home/rgapp/venv/bin/pip install -f /app/whl -c /app/constraints.txt rowerowe_gminy[db]

FROM common as venv-nats-defs
RUN ["python3.12", "-m", "venv", "/home/rgapp/venv"]
COPY --from=build /app/dist/*.whl /app/whl/
COPY --from=build /app/constraints.txt /app/constraints.txt
RUN /home/rgapp/venv/bin/pip install -f /app/whl -c /app/constraints.txt rowerowe_gminy[nats-defs]

FROM common as venv-wha
RUN ["python3.12", "-m", "venv", "/home/rgapp/venv"]
COPY --from=build /app/dist/*.whl /app/whl/
COPY --from=build /app/constraints.txt /app/constraints.txt
RUN /home/rgapp/venv/bin/pip install -f /app/whl -c /app/constraints.txt rowerowe_gminy[wha]

FROM common as venv-wkk
RUN ["python3.12", "-m", "venv", "/home/rgapp/venv"]
COPY --from=build /app/dist/*.whl /app/whl/
COPY --from=build /app/constraints.txt /app/constraints.txt
RUN /home/rgapp/venv/bin/pip install -f /app/whl -c /app/constraints.txt rowerowe_gminy[wkk]

FROM common as venv-worker
RUN ["python3.12", "-m", "venv", "/home/rgapp/venv"]
COPY --from=build /app/dist/*.whl /app/whl/
COPY --from=build /app/constraints.txt /app/constraints.txt
RUN /home/rgapp/venv/bin/pip install -f /app/whl -c /app/constraints.txt rowerowe_gminy[worker]

FROM common as runtime
RUN groupadd -g 1000 rgapp
RUN useradd -ms /bin/bash -u 1000 -g 1000 rgapp
USER rgapp
WORKDIR /home/rgapp/app

FROM runtime as all
COPY --chown=rgapp:rgapp --from=venv-all /home/rgapp/venv /home/rgapp/venv
ENV PATH="/home/rgapp/venv/bin:$PATH"

FROM runtime as api
COPY --chown=rgapp:rgapp --from=venv-api /home/rgapp/venv /home/rgapp/venv
ENV PATH="/home/rgapp/venv/bin:$PATH"
ENTRYPOINT [ "rg-api" ]

FROM runtime as db
COPY --chown=rgapp:rgapp --from=venv-db /home/rgapp/venv /home/rgapp/venv
ENV PATH="/home/rgapp/venv/bin:$PATH"
ENTRYPOINT [ "rg-db" ]

FROM runtime as nats-defs
COPY --chown=rgapp:rgapp --from=venv-nats-defs /home/rgapp/venv /home/rgapp/venv
ENV PATH="/home/rgapp/venv/bin:$PATH"
ENTRYPOINT [ "rg-nats-defs" ]

FROM runtime as wha
COPY --chown=rgapp:rgapp --from=venv-wha /home/rgapp/venv /home/rgapp/venv
ENV PATH="/home/rgapp/venv/bin:$PATH"
ENTRYPOINT [ "rg-wha" ]

FROM runtime as wkk
COPY --chown=rgapp:rgapp --from=venv-wkk /home/rgapp/venv /home/rgapp/venv
ENV PATH="/home/rgapp/venv/bin:$PATH"
ENTRYPOINT [ "rg-wkk" ]

FROM runtime as worker
COPY --chown=rgapp:rgapp --from=venv-worker /home/rgapp/venv /home/rgapp/venv
ENV PATH="/home/rgapp/venv/bin:$PATH"
ENTRYPOINT [ "rg-worker" ]

# DuckDB container
# Requires DuckDB database to be ready
FROM base as geodb
# Local path to DuckDB database
ARG dbpath=./geo.db
COPY ${dbpath} /opt/geo.db
ENV GEO_DB_PATH=/opt/geo.db
RUN chown 1000:1000 /opt/geo.db
