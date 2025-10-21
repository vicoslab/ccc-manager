FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Ljubljana

RUN apt update && apt install -y python3 python3-pip git bash tzdata
RUN pip3 install streamlit streamlit[auth] ruamel-yaml ruamel-yaml-string ansi2html

RUN groupadd user && useradd -m -g user user
RUN install -ouser -guser -d /opt/ccc-manager /opt/ccc-inventory
USER user

RUN git clone https://github.com/vicoslab/ccc-manager /opt/ccc-manager
WORKDIR /opt/ccc-manager

ENTRYPOINT [ "bash", "/opt/ccc-manager/entrypoint.sh" ]