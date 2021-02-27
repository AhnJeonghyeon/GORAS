#!/usr/bin/python3

"""
    This is a module that supports communication with Starcraft II API.
"""

import logging
import websocket

from s2clientprotocol import sc2api_pb2 as sc_pb

FORMAT = '%(asctime)s %(module)s %(levelname)s %(lineno)d %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


class sc2(object):
    def __init__(self):
        self.conn = None
        self.is_connected = False

        # self.log=open("log.txt","w")

    def open(self, address='127.0.0.1', port=5000):
        try:
            self.conn = websocket.create_connection("ws://%s:%s/sc2api" % (address, port), timeout=60)
            self.is_connected = self.conn
            logger.info('sc2 is connected.')
        except Exception as ex:
            logger.error('While connecting to sc2: %s' % (str(ex)))

    def close(self):
        if self.is_connected:
            self.conn.close()

    def send(self, **kwargs):
        request = sc_pb.Request(**kwargs)
        request_str = request.SerializeToString()
        if self.is_connected:
            self.conn.send(request_str)
            return self.read()

    def read(self):
        response_str = self.conn.recv()
        response = sc_pb.Response()
        response.ParseFromString(response_str)
        return response
        #print(response,file=self.log)
        #return

