FROM python:3.10-slim

COPY scripts/install_prereqs.sh /tmp/install_prereqs.sh
RUN /tmp/install_prereqs.sh && rm /tmp/install_prereqs.sh

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir .

CMD ["python"]
