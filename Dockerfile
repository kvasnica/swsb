FROM debian:jessie
MAINTAINER Michal Kvasnica <michal.kvasnica@gmail.com>

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
	curl \
	wget \
	joe \
	unzip \
	zip
RUN apt-get install -y --no-install-recommends \
	python \
	python-pip

RUN apt-get install -y --no-install-recommends \
	python-tornado

WORKDIR /root
COPY *.html swsb.py /root/
EXPOSE 8025
ENTRYPOINT ["python", "swsb.py"]

# docker build -t kvasnica/swsb .

## publish to all intefaces, requires adding firewall rule
## with --iptables=false in /etc/default/docker:
# v-add-firewall-rule ACCEPT 0.0.0.0/0 8025 tcp swsb
# docker run -it -p 8025:8025 kvasnica/swsb

