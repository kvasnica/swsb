FROM python:3-onbuild
MAINTAINER Michal Kvasnica <michal.kvasnica@gmail.com>

WORKDIR /root
COPY swsb.py /root/
EXPOSE 8025
ENTRYPOINT ["python", "swsb.py"]

# docker build -t kvasnica/swsb .
# docker push kvasnica/swsb

## publish to all intefaces, requires adding firewall rule
## with --iptables=false in /etc/default/docker:
# v-add-firewall-rule ACCEPT 0.0.0.0/0 8025 tcp swsb
# docker run -it -p 8025:8025 kvasnica/swsb
