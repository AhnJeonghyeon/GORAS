#! usr/bin/env python3

"""
    dur_test.py
    This File used to show the test result that is the durability of connection among dummies.
        - Results are shown in graph by matplotlib
        - All conditions of test is written on test_cond.txt
        - Includes
                - 'Received msg vs. Total msg'
                - 'Execution Time vs. Total msg'
                - 'Received msg vs. Dummies #'
                - 'Execution Time vs. Dummies #'
                - 'Received msg vs. Sleep Time'
                - 'Received msg vs. Dummy # with Random Sleep Time'
        - Save as .png file, you may check it under results folder.
"""

import matplotlib.pyplot as plt
import numpy as np

import json

#- 'Received msg vs. Total msg'
with open('recv_msg_total','r') as file:
    totalmsg=[]
    recvmsg=[]

    fig=plt.figure(1)

    cnt=0
    json_block = []

    for line in file:

        # Add the line to our JSON block
        json_block.append(line)

        # Check whether we closed our JSON block
        if line.startswith('}'):
            cnt+=1
            # Do something with the JSON dictionary
            json_dict = json.loads(''.join(json_block))
            #print(json_dict)
            totalmsg.append(json_dict['totalmsg#'])
            recvmsg.append(json_dict['recvmsg#'])

            # Start a new block
            json_block = []

    y_pos=np.arange(cnt)
    bar = plt.bar(y_pos,recvmsg)

    for rect in bar:
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width()/2.0, height, '%d' % int(height), ha='center', va='bottom')

    plt.xlabel('Total Message #')
    plt.xticks(y_pos, totalmsg)
    plt.ylabel('Received Message #')
    plt.title('Received Message versus Total')
    #plt.show()
    plt.savefig('./results/recv_total.png')

#- 'Execution Time vs. Total msg'
with open('exec_time_total','r') as file:
    totalmsg=[]
    exectime=[]

    fig = plt.figure(2)

    cnt=0
    json_block = []

    for line in file:

        # Add the line to our JSON block
        json_block.append(line)

        # Check whether we closed our JSON block
        if line.startswith('}'):
            cnt+=1
            # Do something with the JSON dictionary
            json_dict = json.loads(''.join(json_block))
            #print(json_dict)
            totalmsg.append(json_dict['totalmsg#'])
            exectime.append(json_dict['time'])

            # Start a new block
            json_block = []

    y_pos=np.arange(cnt)
    bar = plt.bar(y_pos,exectime)

    for rect in bar:
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width()/2.0, height, '%d' % int(height), ha='center', va='bottom')

    plt.xlabel('Total Message #')
    plt.xticks(y_pos, totalmsg)
    plt.ylabel('Execution Time(s)')
    plt.title('Execution Time versus Total')
    # plt.show()
    plt.savefig('./results/time_total.png')

#- 'Received msg vs. Dummies #'
with open('recv_msg_dummy','r') as file:
    dummy=[]
    recvmsg=[]

    fig = plt.figure(3)

    cnt=0
    json_block = []

    for line in file:

        # Add the line to our JSON block
        json_block.append(line)

        # Check whether we closed our JSON block
        if line.startswith('}'):
            cnt+=1
            # Do something with the JSON dictionary
            json_dict = json.loads(''.join(json_block))
            #print(json_dict)
            dummy.append(json_dict['dummy#'])
            recvmsg.append(json_dict['recvmsg#'])

            # Start a new block
            json_block = []

    y_pos=np.arange(cnt)
    bar = plt.bar(y_pos,recvmsg)

    for rect in bar:
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width()/2.0, height, '%d' % int(height), ha='center', va='bottom')

    plt.xlabel('Dummy #')
    plt.xticks(y_pos, dummy)
    plt.ylabel('Received Message #')
    plt.title('Received Message versus Dummies')
    # plt.show()
    plt.savefig('./results/recv_dummy.png')

#- 'Execution Time vs. Dummies #'
with open('recv_msg_dummy','r') as file:
    dummy=[]
    recvmsg=[]
    exectime = []

    fig_recv = plt.figure(3)

    cnt=0
    json_block = []

    for line in file:

        # Add the line to our JSON block
        json_block.append(line)

        # Check whether we closed our JSON block
        if line.startswith('}'):
            cnt+=1
            # Do something with the JSON dictionary
            json_dict = json.loads(''.join(json_block))
            #print(json_dict)
            dummy.append(json_dict['dummy#'])
            recvmsg.append(json_dict['recvmsg#'])
            exectime.append(json_dict['time'])

            # Start a new block
            json_block = []

    y_pos=np.arange(cnt)
    bar = plt.bar(y_pos,recvmsg)

    for rect in bar:
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width()/2.0, height, '%d' % int(height), ha='center', va='bottom')

    plt.xlabel('Dummy #')
    plt.xticks(y_pos, dummy)
    plt.ylabel('Received Message #')
    plt.title('Received Message versus Dummies')
    # plt.show()
    plt.savefig('./results/recv_dummy.png')

    fig_time = plt.figure(4)

    y_pos = np.arange(cnt)
    bar = plt.bar(y_pos, exectime)

    for rect in bar:
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width() / 2.0, height, '%d' % int(height), ha='center', va='bottom')

    plt.xlabel('Dummy #')
    plt.xticks(y_pos, dummy)
    plt.ylabel('Execution Time(s)')
    plt.title('Execution Time versus Dummies')
    # plt.show()
    plt.savefig('./results/time_dummy.png')

#- 'Received msg vs. Sleep Time'
with open('recv_msg_sleep','r') as file:
    sleeptime=[]
    recvmsg=[]

    fig = plt.figure(5)

    cnt=0
    json_block = []

    for line in file:

        # Add the line to our JSON block
        json_block.append(line)

        # Check whether we closed our JSON block
        if line.startswith('}'):
            cnt+=1
            # Do something with the JSON dictionary
            json_dict = json.loads(''.join(json_block))
            #print(json_dict)
            sleeptime.append(int(json_dict['test#'])/10)
            recvmsg.append(json_dict['recvmsg#'])

            # Start a new block
            json_block = []

    y_pos=np.arange(cnt)
    bar = plt.bar(y_pos,recvmsg)

    for rect in bar:
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width()/2.0, height, '%d' % int(height), ha='center', va='bottom')

    plt.xlabel('Sleep time')
    plt.xticks(y_pos, sleeptime)
    plt.ylabel('Received Message #')
    plt.title('Received Message versus Sleep Time')
    # plt.show()
    plt.savefig('./results/recv_sleep.png')

with open('recv_msg_sleep_rand','r') as file:
    dummy=[]
    missed=[]

    fig = plt.figure(6)

    cnt=0
    json_block = []

    for line in file:

        # Add the line to our JSON block
        json_block.append(line)

        # Check whether we closed our JSON block
        if line.startswith('}'):
            cnt+=1
            # Do something with the JSON dictionary
            json_dict = json.loads(''.join(json_block))
            #print(json_dict)
            dummy.append(int(json_dict['dummy#']))
            missed.append(int(json_dict['totalmsg#'])-int(json_dict['recvmsg#']))

            # Start a new block
            json_block = []

    y_pos=np.arange(cnt)
    bar = plt.bar(y_pos,missed)

    for rect in bar:
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width()/2.0, height, '%d' % int(height), ha='center', va='bottom')

    plt.xlabel('Dummy #')
    plt.xticks(y_pos, dummy)
    plt.ylabel('Missed Message #')
    plt.title('Missed Message versus Dummy # with Random Sleep Time')
    # plt.show()
    plt.savefig('./results/recv_sleep_rand.png')