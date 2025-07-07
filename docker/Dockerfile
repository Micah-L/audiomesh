FROM python:3.10-slim

# Install JACK server and jacktrip for network audio streaming
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends \
        jackd2 \
        jacktrip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir .

CMD ["python"]
