FROM ubuntu:22.04

RUN apt update && apt install -y python3 python3-pip git bash
RUN pip3 install streamlit streamlit[auth] ruamel-yaml ruamel-yaml-string ansi2html

WORKDIR /opt/ccc-manager

ENTRYPOINT [ "bash", "/opt/ccc-manager/entrypoint.sh" ]