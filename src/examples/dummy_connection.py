#!/usr/bin/python3

"""
    Class DummyThread
    This dummy communicates with the agent,
        - receive a message from the agent and check the agent's task
        - send a message(result) to the agent after checking the agent's message

    The agents need to change their goal state to Achieved/Failed state
    when the task is completed.

    Class Dummy
    This class is simplest version of Agent.
    This Only contains the essential core code to communicate each other.

"""

import sys
import threading
import time
import random
import logging
from datetime import datetime

sys.path.append('../')
from utils.communicator import Communicator, proxy

FORMAT = '%(asctime)s %(module)s %(levelname)s %(lineno)d %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)

TEST_NUM=1
SLEEP_TIME=1.0 #if SLEEP_TIME is zero, it means random.

count_dummy=3
total_msg=10
recv_msg=0

class DummyThread(threading.Thread):
    def __init__(self, name, counter,core=False):
        logging.info(name+' Thread starts initializing...')

        threading.Thread.__init__(self)
        self.threadID = counter
        self.name = name
        self.who=Dummy(self.name)
        self.who.init_comm_agents(core)

        logging.info(self.name+' is Initialzied')

    def run(self):

        logging.info(self.name+' is started to run')
        cnt = 1
        wordorg="HI"
        while True:
            logging.info(self.name+' is running %d loop'%cnt)
            word=wordorg+' #'+str(cnt)
            if cnt > total_msg:
                break

            for i in range(count_dummy):
                self.who.perceive()

            # broadcasting
            self.who.tell(word)

            cnt += 1

            t=SLEEP_TIME
            if t==0:
                t=random.randrange(1,10)
                t/=10
            time.sleep(t)

        self.who.print_res()

class Dummy(object):
    def __init__(self,name):

        self.name=name
        self.count_sent=[0 for i in range(count_dummy)]
        self.count_recv=[0 for i in range(count_dummy)]
        self.filename_sent='./../../test/connection_dur_test/dummy_log/'+name+'_sent.txt'
        self.filename_recv='./../../test/connection_dur_test/dummy_log/'+name+'_recv.txt'
        self.file_sent=open(self.filename_sent,'w')
        self.file_recv=open(self.filename_recv,'w')

    def init_comm_agents(self,core=False):
        self.comm_agents = Communicator(core)

    def deinit_comm_agents(self):
        self.comm_agents.close()

    def perceive(self):
        message = self.comm_agents.read()
        if message:
            t=datetime.now()
            print("Got message / Got Time: "+str(t)+" From\t" + message,file=self.file_recv)
            idx=''.join(x for x in message.split('/')[0] if x.isdigit())
            if idx.isdigit()==True:
                self.count_recv[int(idx)-1]+=1

    def tell(self, statement):
        t=datetime.now()
        msg=self.name+'/ Sent Time: '+str(t)+'/ Msg: '+statement
        print(self.name+"\tis telling to everyone "+msg,file=self.file_sent)
        for i in range(count_dummy):
            self.count_sent[i]+=1
        self.comm_agents.send(msg)

    def print_res(self):
        global recv_msg
        print(self.name)
        for i in range(count_dummy):
            print('\t'+self.name+' sent msg to \t\t%5d #: %d'%(i+1,self.count_sent[i]))
            print('\t'+self.name+' recv msg from \t%5d #: %d'%(i+1,self.count_recv[i]))
            recv_msg+=self.count_recv[i]
        self.file_sent.close()
        self.file_recv.close()

"""
    For testing
"""
RECORD_TEST = False

if __name__ == '__main__':


    value_dict={}
    value_dict['test#']=TEST_NUM
    value_dict['dummy#']=count_dummy
    value_dict['recvmsg#']=0
    value_dict['totalmsg#']=total_msg*count_dummy*count_dummy
    value_dict['time']=0

    start_time=time.time()
    threads=[]

    proxy_thread = threading.Thread(target=proxy)

    based_name='dummy'
    counter=1
    for i in range(count_dummy-1):
        name=based_name+str(i+1)
        threads.append(DummyThread(name,counter))
        counter+=1

    #Add CoreThread
    name=based_name+'core3'
    threads.append(DummyThread(name,counter,core=True))

    # Wait for thread initialization
    time.sleep(1)

    proxy_thread.start()

    time.sleep(1) # wait for turn on proxy

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads exit
    for thread in threads:
        thread.join()

    execution_time=time.time()-start_time
    value_dict['time']=execution_time
    print("Execution Time : %s seconds"%(execution_time))

    value_dict['recvmsg#']=recv_msg
    print("Received # : %d"%recv_msg)

    if RECORD_TEST==True:
        import json
        with open('./../../test/connection_dur_test/recv_msg_sleep_rand', 'a') as logfile:
            json.dump(value_dict,logfile, indent=4, sort_keys=True,separators=(',', ': '))
            print('',file=logfile)
