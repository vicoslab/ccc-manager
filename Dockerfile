FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Ljubljana

RUN apt update && apt install -y python3 python3-pip git bash tzdata
RUN pip3 install streamlit streamlit[auth] ruamel-yaml ruamel-yaml-string ansi2html

WORKDIR /opt/ccc-manager

ENTRYPOINT [ "bash", "/opt/ccc-manager/entrypoint.sh" ]