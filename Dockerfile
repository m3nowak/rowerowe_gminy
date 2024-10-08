FROM docker.io/library/almalinux:9 AS common
LABEL org.opencontainers.image.source="https://github.com/m3nowak/rowerowe_gminy"
LABEL org.opencontainers.image.description="Rowerowe Gminy"
LABEL org.opencontainers.image.licenses=Apache-2.0

RUN ["dnf", "install", "-y", "python3.12", "python3.12-pip"]

FROM common AS build
RUN ["python3.12", "-m", "pip", "install", "pdm"]
COPY . /app
WORKDIR /app
RUN ["pdm", "build"]

FROM common as venv-api
RUN ["python3.12", "-m", "venv", "/home/rgapp/venv"]
COPY --from=build /app/dist/*.whl /app/whl/
RUN /home/rgapp/venv/bin/pip install -f /app/whl rowerowe_gminy[api]

FROM common as venv-wha
RUN ["python3.12", "-m", "venv", "/home/rgapp/venv"]
COPY --from=build /app/dist/*.whl /app/whl/
RUN /home/rgapp/venv/bin/pip install -f /app/whl rowerowe_gminy[wha]

FROM common as venv-wkk
RUN ["python3.12", "-m", "venv", "/home/rgapp/venv"]
COPY --from=build /app/dist/*.whl /app/whl/
RUN /home/rgapp/venv/bin/pip install -f /app/whl rowerowe_gminy[wkk]

FROM common as runtime
RUN groupadd -g 1000 rgapp
RUN useradd -ms /bin/bash -u 1000 -g 1000 rgapp
USER rgapp
WORKDIR /home/rgapp/app

FROM runtime as api
COPY --chown=rgapp:rgapp --from=venv-api /home/rgapp/venv /home/rgapp/venv
ENV PATH="/home/rgapp/venv/bin:$PATH"
ENTRYPOINT [ "rg-api", "run" ]

FROM runtime as wha
COPY --chown=rgapp:rgapp --from=venv-wha /home/rgapp/venv /home/rgapp/venv
ENV PATH="/home/rgapp/venv/bin:$PATH"
ENTRYPOINT [ "rg-wha" ]

FROM runtime as wkk
COPY --chown=rgapp:rgapp --from=venv-wkk /home/rgapp/venv /home/rgapp/venv
ENV PATH="/home/rgapp/venv/bin:$PATH"
ENTRYPOINT [ "rg-wkk" ]