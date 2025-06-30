FROM python:3.12-bookworm AS runner

# All-in one Dockerfile for testing

RUN pip install uv

ARG PRJDIR=/tw APPDIR=${PRJDIR}/src
ENV PATH="${PRJDIR}/.venv/bin:$PATH" \
    VIRTUAL_ENV=${PRJDIR}/.venv
ENV TASKRC=${APPDIR}/pytaskrc TASKDATA=/tw/.task  PYTHONPATH=$APPDIR
# Install Taskwarrior
COPY taskwarrior.bin/task /usr/local/bin
COPY src $APPDIR
COPY uv.lock pyproject.toml tests $PRJDIR
COPY .venv $PRJDIR/.venv

WORKDIR $APPDIR
