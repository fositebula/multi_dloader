# coding=utf-8
import time

import signal
from twisted.internet import protocol, reactor
import json
import os
import fcntl
import copy
from multiprocessing import Process

CONF_FILE = 'USBPortInfo.json'
PORT = 21567
OLD_USBS = []
TIME_OUT = 1500

class NoUSBInfoConfig(Exception):
    pass

class TSServProtocol(protocol.Protocol):
    dloader_pids = {}
    def connectionMade(self):
        usb_change_flag = False
        clnt = self.clnt = self.transport.getPeer().port
        print '...conneting from:', clnt
        if not os.path.exists(CONF_FILE):
            raise NoUSBInfoConfig('There is no '+CONF_FILE)

        with open(CONF_FILE, 'r+', buffering=0) as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            data = json.load(f)
            time_out = TIME_OUT
            #如果有变化了再执行下边的语句
            while not usb_change_flag and time_out:
                #5分钟内检测不到就不检测了,并且给客户端发送timeout
                time_out -= 1
                dev_usbs = filter(lambda x: 'ttyUSB' in x, os.listdir('/dev/'))
                time.sleep(0.2)
                # print 'data ', dev_usbs, ' ', data.get('old_usb'), time_out
                if set(dev_usbs) != set(data.get('old_usb')):
                    new_usb = set(dev_usbs) - set(data.get('old_usb'))
                    print new_usb
                    data['old_usb'] = copy.copy(dev_usbs)
                    #不用关减少的,只需要把增加的USB检测出来后发出去
                    if not new_usb:
                        continue
                    print 'after copy: ', data.get('old_usb')
                    usb_change_flag = True
            if time_out:
                print '检测到有新的usb产生', new_usb
                n_usb = new_usb.pop()
                self.transport.write(n_usb.encode('utf-8'))
                data[n_usb]= {'used': True, 'who': clnt}
            else:
                self.transport.write('time_out'.encode('utf-8'))

            print data, clnt
            #将最新的数据更新到文件中
            f.seek(0)
            f.truncate()
            json.dump(data, f)
            f.flush()

            fcntl.flock(f, fcntl.LOCK_UN)

    def dataReceived(self, data):
        print '####',data
        self.dloader_pids[self.clnt] = data

    def connectionLost(self, reason):
        print self.dloader_pids.get(self.clnt)
        if self.dloader_pids.get(self.clnt):
            print 'kill: ', self.dloader_pids.get(self.clnt)
            os.kill(int(self.dloader_pids[self.clnt]), signal.SIGKILL)
        pass
        # os.kill(self.dloader_pid, os.SIGKILL)
        # clnt = self.clnt = self.transport.getPeer().port
        # print 'lost client '+str(clnt)
        #
        # used_usb = ''
        # with open(CONF_FILE, 'r+', buffering=0) as f:
        #     fcntl.flock(f, fcntl.LOCK_EX)
        #     data = json.load(f)
        #     for k, v in data.iteritems():
        #         if isinstance(v, list):
        #             continue
        #         if str(v['who']) == str(clnt):
        #             used_usb = k
        #             break
        #     fcntl.flock(f, fcntl.LOCK_UN)
        #
        # while True:
        #     dev_usbs = filter(lambda x: 'ttyUSB' in x, os.listdir('/dev/'))
        #     if used_usb in dev_usbs:
        #         time.sleep(0.2)
        #         continue
        #     with open(CONF_FILE, 'r+', buffering=0) as f:
        #         fcntl.flock(f, fcntl.LOCK_EX)
        #         data = json.load(f)
        #         if data.has_key(used_usb):
        #             data.pop(used_usb)
        #         if used_usb in data['old_usb']:
        #             data['old_usb'].remove(used_usb)
        #         f.seek(0)
        #         f.truncate()
        #         json.dump(data, f)
        #         f.flush()
        #         fcntl.flock(f, fcntl.LOCK_UN)
        #         break

def init():
    with open(CONF_FILE, 'w+', buffering=0) as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        dev_usbs = filter(lambda x: 'ttyUSB' in x, os.listdir('/dev/'))
        data = {'old_usb':[]}
        data['old_usb'] = copy.copy(dev_usbs)
        f.seek(0)
        f.truncate()
        json.dump(data, f)
        f.flush()
        fcntl.flock(f, fcntl.LOCK_UN)

def scan_dev_ttyUSBX():
    print 'scan_dev_ttyUSBX started'
    while True:
        with open(CONF_FILE, 'r+', buffering=0) as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            dev_usbs = filter(lambda x: 'ttyUSB' in x, os.listdir('/dev/'))
            data = json.load(f)
            # print set(dev_usbs) != set(data['old_usb'] )
            # print not (set(dev_usbs) - set(data['old_usb'] ))
            # print set(dev_usbs), set(data['old_usb'])
            if set(dev_usbs) != set(data['old_usb'] ) and not set(dev_usbs) - set(data['old_usb']):
                print 'update'
                data['old_usb'] = copy.copy(dev_usbs)
                f.seek(0)
                f.truncate()
                json.dump(data, f)
                f.flush()
            fcntl.flock(f, fcntl.LOCK_UN)
        time.sleep(1)


if __name__ == '__main__':
    init()
    process = Process(target=scan_dev_ttyUSBX, name='scan_dev_ttyUSBX')
    process.start()
    factory = protocol.Factory()
    factory.protocol = TSServProtocol
    print 'waiting for connecting...'
    reactor.listenTCP(PORT, factory)
    reactor.run()
    process.join()

