FROM python:3.12-bookworm
# All-in one Dockerfile for testing

RUN apt update && apt update && apt install taskwarrior && pip install uv

ARG PRJDIR=/tw APPDIR=${PRJDIR}/src
ENV PATH="${PRJDIR}/.venv/bin:$PATH" \
    VIRTUAL_ENV=${PRJDIR}/.venv
ENV TASKRC=${APPDIR}/api_taskrc TASKDATA=/tw/.task  PYTHONPATH=$APPDIR
WORKDIR $APPDIR
