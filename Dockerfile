FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Ljubljana

RUN apt update && apt install -y python3 python3-pip git bash tzdata cron
RUN pip3 install streamlit streamlit[auth] ruamel-yaml ruamel-yaml-string ansi2html

RUN chmod u+s /usr/sbin/cron

RUN groupadd user && useradd -m -g user user
RUN install -ouser -guser -d /opt/ccc-manager /opt/ccc-inventory
USER user

RUN git clone --depth 1 https://github.com/vicoslab/ccc-manager /opt/ccc-manager
WORKDIR /opt/ccc-manager

RUN python3 image_info.py
RUN echo "* * * * 0 cd /opt/ccc-manager && python3 image_info.py /opt/ccc-manager/docker-image.cache.txt >/proc/1/fd/1 2>/proc/1/fd/2" > image_info.cron \
    && crontab -u user image_info.cron

ENTRYPOINT [ "bash", "/opt/ccc-manager/entrypoint.sh" ]