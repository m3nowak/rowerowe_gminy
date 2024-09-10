FROM docker.io/library/almalinux:9 AS common
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

FROM common as api
RUN groupadd -g 1000 rgapp
RUN useradd -ms /bin/bash -u 1000 -g 1000 rgapp
USER rgapp
WORKDIR /home/rgapp/app
COPY --chown=rgapp:rgapp --from=venv-api /home/rgapp/venv /home/rgapp/venv
ENV PATH="/home/rgapp/venv/bin:$PATH"
CMD rg-api