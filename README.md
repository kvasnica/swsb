# swsb
Simple WebSocket Broker

[![Code Climate](https://codeclimate.com/github/kvasnica/swsb/badges/gpa.svg)](https://codeclimate.com/github/kvasnica/swsb)

## Build for Docker
```
docker build -t kvasnica/swsb .
```

## Run via Docker
```
docker run -it -p 8025:8025 kvasnica/swsb
```

## Usage

Connect your websocket client(s) to `ws://127.0.0.1:8025/t/TOPIC`, where `TOPIC` is any string (including `MAINTOPIC/SUBTOPIC/...`). Anything sent to the websocket will be broadcasted to all other connected clients.
