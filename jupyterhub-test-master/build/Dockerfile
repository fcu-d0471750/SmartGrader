FROM ubuntu:16.04

FROM alpine:3.8

COPY --from=0 /etc/apt/sources.list /etc/apt/sources.list

RUN apk add --no-cache curl jq && \
    export COUNTRY=$(curl ipinfo.io | jq '.country' | tr -d '"') && \
    sed -i "s|http:\/\/archive|http:\/\/$COUNTRY.archive|g" /etc/apt/sources.list
#"

FROM jupyterhub/jupyterhub:1.0.0

COPY --from=1 /etc/apt/sources.list /etc/apt/sources.list

# install necessary package
RUN pip install notebook==6.0.1
RUN pip install oauthenticator==0.9.0

# install custom package
RUN pip install nbgrader && \
    pip install pandas

# change notebook js to SmartGrader js
COPY ./main.min.js /opt/conda/lib/python3.6/site-packages/notebook/static/notebook/js

RUN apt-get update && \
    apt-get -y install sudo && \
    apt-get install vim

# add a sudo user
RUN sudo useradd --create-home admin && \
    sudo groupadd -g 245 jupyterhub && \
    sudo adduser admin sudo && \
    sudo adduser admin jupyterhub
