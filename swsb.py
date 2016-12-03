'''
Simple Websocket Broker

Copyright (c) 2014-2016 Michal Kvasnica, michal.kvasnica@gmail.com
'''

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import tornado.template
import json
import logging
import argparse
from datetime import datetime

# parse command-line inputs
parser = argparse.ArgumentParser(description='Simple WebSockets Broker.')
parser.add_argument('--port', '-p', default=8025, type=int,
    help='port number (default is 8025)')
parser.add_argument('--loglevel', '-l', default='info', choices=['error', 'info', 'debug'],
    help='logging level (error|info|debug)')
parser.add_argument('--maxclients', '-m', default=1000, type=int,
    help='maximal number of clients (default is 1000)')
parser.add_argument('--statusperiod', '-s', default=3600, type=int,
    help='status report period in seconds (default is 3600)')
parser.add_argument('--cleanupperiod', '-c', default=3600, type=int,
    help='cleanup period in seconds (default is 3600)')
parser.add_argument('--hostname', '-n',
    help='hostname of the server including protocol for cross-domain ajax')
parser.add_argument('--password', '-w',
    help='password for admin access (if undefined, admin access is disabled)')

"letmein"
args = parser.parse_args()

logging.basicConfig(
format='[%(asctime)s] %(levelname)s:%(filename)s:%(funcName)s: %(message)s', level=logging.ERROR)

logger = logging.getLogger('SWSB')
if args.loglevel=='error':
    logger.setLevel(logging.ERROR)
elif args.loglevel=='info':
    logger.setLevel(logging.INFO)
else:
    logger.setLevel(logging.DEBUG)

# maximum number of clients
MAX_CLIENTS = args.maxclients
# status report period in seconds
STATUS_PERIOD = args.statusperiod
# empty topic cleanup period in seconds
CLEANUP_PERIOD = args.cleanupperiod

class Topic:
    def __init__(self, id):
        '''
        Creates a new topic
        '''

        self.ID = id
        self.Clients = {}
        self.CreatedOn = datetime.now()
        logger.info("New topic: %s", self.ID)

    def shutdown(self, reason=""):
        # disconnect all connected clients
        logger.info("Shutting down topic \"%s\"%s", self.ID, reason)
        for client in self.Clients.values():
            client.error("SWSB: Topic \"%s\" shuts down%s" % (self.ID, reason))
            client.shutdown()

    def addClient(self, client):
        # registers a new client of this topic
        logger.debug("Topic/addClient: %s, client: %s", self.ID, client.SocketKey)
        self.Clients[client.SocketKey] = client

    def removeClient(self, client):
        # removes a particular client from this topic
        logger.debug("Topic/removeClient: %s, client: %s", self.ID, client.SocketKey)
        self.Clients.pop(client.SocketKey, None)

    def broadcast(self, source, message):
        # broadcasts MESSAGE to all clients connected to this topic except of SOURCE
        for id, client in self.Clients.items():
            # do not broadcast to self
            if id != source.SocketKey:
                logger.debug("Topic/broadcast: from: %s, to: %s, message: %s", source.SocketKey, client.SocketKey, message)
                client.send(message)

class TopicManager:
    def __init__(self):
        self.Topics = {}

    def createTopic(self, id):
        logger.debug("TopicManager/createTopic: ID: %s", id)
        topic = Topic(id)
        self.Topics[id] = topic
        return topic

    def removeTopic(self, id, reason=""):
        logger.debug("TopicManager/createTopic: ID: %s, reason: %s", id, reason)
        topic = self.Topics[id]
        topic.shutdown(reason)
        self.Topics.pop(id, None)

    def getTopic(self, id):
        if id in self.Topics.keys():
            return self.Topics[id]
        else:
            # create a new topic
            return self.createTopic(id)

    def status(self):
        logger.info("Number of active topics: %d" % len(self.Topics))

    def cleanup(self):
        # removes all topics with no clients
        logger.debug("TopicManager/cleanup")
        for id, topic in self.Topics.items():
            if len(topic.Clients)==0:
                self.removeTopic(id, " (no clients)")

class Client:
    def __init__(self, socket, topic):
        self.Socket = socket
        self.SocketKey = socket.request.headers["Sec-Websocket-Key"]
        self.IP = socket.request.remote_ip
        self.Topic = topic
        self.CreatedOn = datetime.now()
        logger.info("Client connected: IP: %s, Topic: %s", self.IP, self.Topic.ID)

    def shutdown(self):
        logger.info("Client disconnected: IP: %s, Topic: %s", self.IP, self.Topic.ID)
        self.Topic.removeClient(self)
        self.disconnect()

    def disconnect(self):
        try:
            self.Socket.close()
            return True
        except AttributeError:
            return False

    def read(self, message):
        logger.debug("Client IP: %s, Topic: %s, Received: %s", self.IP, self.Topic.ID, message)
        self.Topic.broadcast(self, message)

    def send(self, message):
        self.Socket.write_message(message)

    def error(self, message):
        self.Socket.write_message(message)

class ClientManager:
    def __init__(self):
        self.Clients = {}

    def addClient(self, socket, topic):
        '''
        Adds a new websocket client for the desired topic
        '''
        if len(self.Clients) >= MAX_CLIENTS:
            # maximal number of clients reached
            logger.info("Maximum number of clients reached.")
            socket.write_message("SWSB: Maximum number of clients reached.")
            socket.close()
            return None
        client = Client(socket, topic)
        topic.addClient(client)
        self.Clients[client.SocketKey] = client
        return client

    def removeClient(self, socket):
        client = self.getClient(socket=socket)
        if client:
            client.shutdown()
            self.Clients.pop(client.SocketKey, None)

    def getClient(self, socket=None, socket_key=None):
        if socket:
            socket_key = socket.request.headers["Sec-Websocket-Key"]
        if socket_key in self.Clients.keys():
            return self.Clients[socket_key]
        else:
            return None

    def status(self):
        logger.info("Active clients: %d" % len(self.Clients))

class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self, id):
        # creates the topic if necessary
        topic = TopicManager.getTopic(id)
        if topic is None:
            # no such topic
            self.write_message("SWSB: No such topic %s" % id)
            self.close()
            return
        ClientManager.addClient(self, topic)

    def on_message(self, message):
        # receives data from the socket
        client = ClientManager.getClient(socket=self)
        if client:
            client.read(message)

    def on_close(self):
        ClientManager.removeClient(socket=self)

class WSEchoHandler(tornado.websocket.WebSocketHandler):
    def on_message(self, message):
        # receives data from the socket
        self.write_message(message)

class AdminHandler(tornado.web.RequestHandler):
    def get(self):
        pin = self.get_argument("pw", "")
        if not args.password or pin != args.password:
            self.send_error(403)
            return
        self.render("./admin.html", TopicManager=TopicManager)

class TopicHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        if args.hostname:
            self.set_header("Access-Control-Allow-Origin", SWSB_HOST)

    def get(self, action, id=None):
        if action=="remove":
            if id in TopicManager.Topics.keys():
                TopicManager.removeTopic(id, " (web request)")
                self.write("Topic \"%s\" was removed." % id)
            else:
                self.write("No such topic \"%s\"" % id)

        elif action=="list":
            self.write(str(TopicManager.Topics.keys()))

        else:
            self.send_error(400)

ClientManager = ClientManager()
TopicManager = TopicManager()
settings = {}

application = tornado.web.Application([
    (r'/t/(.*)', WSHandler),
    (r'/test/echo', WSEchoHandler),
    (r'/m/topic/(\w+)/(.*)', TopicHandler),
    (r'/a', AdminHandler),
    (r'/html/(.*)', tornado.web.StaticFileHandler, {'path': './html'}),
], **settings)

if __name__ == "__main__":
    print("Simple websocket broker running on port %d..." % args.port)
    if args.password:
        print("Password: %s" % args.password)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(args.port)
    tornado.ioloop.PeriodicCallback(TopicManager.cleanup, CLEANUP_PERIOD*1000).start()
    tornado.ioloop.PeriodicCallback(ClientManager.status, STATUS_PERIOD*1000).start()
    tornado.ioloop.PeriodicCallback(TopicManager.status, STATUS_PERIOD*1000).start()
    tornado.ioloop.IOLoop.instance().start()
    print("...done")
