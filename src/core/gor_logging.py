#!/usr/bin/env python3

'''
    Logging module for data analysis
'''
import sys
sys.path.append('..')
from utils.communicator import Communicator
from threading import Thread

import datetime
import time

datetime_format = '%Y-%m-%d %H:%M:%S.%f'

class GorasLogging(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.logs = []
        self.listener = Communicator(topic='logging')
        self.is_alive = True
        self.log_file = open('/tmp/latest_simulation.txt', 'w')

    def close(self):
        self.log_file.close()
        self.is_alive = False
        self.join()

    def run(self):
        while self.is_alive:
            message = self.listener.read()
            if message == '':
                time.sleep(0.1)
                continue
            log_message = '{}\t{}\t\r\n'.format(datetime.datetime.now().isoformat(timespec='microseconds'), message)
            # Where to store?
            self.log_file.write(log_message)

if __name__ == '__main__':
    logger = GorasLogging()
    try:
        logger.run()
    except KeyboardInterrupt:
        pass
    logger.close()
