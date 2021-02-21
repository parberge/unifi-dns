FROM python:3.9-alpine
RUN apk --no-cache add dnsmasq~=2
RUN pip install requests==2.*

WORKDIR /app
COPY *.py ./
COPY run.sh ./

EXPOSE 53 53/udp
CMD ["./run.sh"]
