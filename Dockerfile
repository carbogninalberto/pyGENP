FROM python:3.8.5-buster

WORKDIR /app
COPY . .

RUN apt-get update

RUN echo -e "BASE_NS3_PATH=\"/app/ns3/ns-allinone-3.32/ns-3.32\"\nCPUS=4" > /app/.env
RUN cd /app/ns3/ns-allinone-3.32/ns-3.32/ && ./waf configure

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENTRYPOINT [ "python" ]
CMD ["server.py" ]