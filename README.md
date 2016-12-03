# swsb
Simple WebSocket Broker

[![Code Climate](https://codeclimate.com/github/kvasnica/swsb/badges/gpa.svg)](https://codeclimate.com/github/kvasnica/swsb)

## Run via Docker
```
docker run -it -p 8025:8025 kvasnica/swsb
```

## Run locally

1. Install [tornado](http://www.tornadoweb.org) (e.g. via `pip install tornado`)
2. Run `python swsb.py`

Both python2 and python3 are supported.

## Usage

Connect your websocket client(s) to `ws://127.0.0.1:8025/t/TOPIC`, where `TOPIC` is any string (including `MAINTOPIC/SUBTOPIC/...`). Anything sent to the websocket will be broadcasted to all other connected clients.

```
$ python swsb.py --help
usage: swsb.py [-h] [--port PORT] [--loglevel {error,info,debug}]
               [--maxclients MAXCLIENTS] [--statusperiod STATUSPERIOD]
               [--cleanupperiod CLEANUPPERIOD]

Simple WebSockets Broker.

optional arguments:
  -h, --help            show this help message and exit
  --port PORT, -p PORT  port number (default is 8025)
  --loglevel {error,info,debug}, -l {error,info,debug}
                        logging level (error|info|debug)
  --maxclients MAXCLIENTS, -m MAXCLIENTS
                        maximal number of clients (default is 1000)
  --statusperiod STATUSPERIOD, -s STATUSPERIOD
                        status report period in seconds (default is 3600)
  --cleanupperiod CLEANUPPERIOD, -c CLEANUPPERIOD
                        cleanup period in seconds (default is 3600)
```
