# coding=utf-8
import time
from twisted.internet import protocol, reactor
import json
import os
import fcntl
import copy

CONF_FILE = 'USBPortInfo.json'
PORT = 21567
OLD_USBS = []

class NoUSBInfoConfig(Exception):
    pass

class TSServProtocol(protocol.Protocol):
    def connectionMade(self):
        usb_change_flag = False

        clnt = self.clnt = self.transport.getPeer().port
        print '...conneting from:', clnt
        if not os.path.exists(CONF_FILE):
            raise NoUSBInfoConfig('There is no '+CONF_FILE)

        with open(CONF_FILE, 'r+') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            data = json.load(f)
            #如果有变化了再执行下边的语句
            while not usb_change_flag:
                dev_usbs = filter(lambda x: 'ttyUSB' in x, os.listdir('/dev/'))
                time.sleep(0.2)
                print 'data ', dev_usbs, ' ', data.get('old_usb')
                if dev_usbs != data.get('old_usb'):
                    new_usb = set(dev_usbs) - set(data.get('old_usb'))
                    data['old_usb'] = copy.copy(dev_usbs)
                    #usb减少了
                    if not new_usb:
                        continue
                    print 'after copy: ', data.get('old_usb')
                    usb_change_flag = True
            print '检测到有新的usb产生', new_usb
            n_usb = new_usb.pop()
            self.transport.write(n_usb.encode('utf-8'))

            print data, clnt
            data[n_usb]= {'used':True, 'who':clnt}
            #将最新的数据更新到文件中
            f.seek(0)
            f.truncate()
            json.dump(data, f)
            f.flush()

            fcntl.flock(f, fcntl.LOCK_UN)

    def connectionLost(self, reason):
        clnt = self.clnt = self.transport.getPeer().port
        print 'lost client '+str(clnt)

        used_usb = ''
        with open(CONF_FILE, 'r+') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            data = json.load(f)
            for k, v in data.iteritems():
                if isinstance(v, list):
                    continue
                if str(v['who']) == str(clnt):
                    used_usb = k
                    break
            fcntl.flock(f, fcntl.LOCK_UN)

        while True:
            dev_usbs = filter(lambda x: 'ttyUSB' in x, os.listdir('/dev/'))
            if used_usb in dev_usbs:
                time.sleep(0.2)
                continue
            with open(CONF_FILE, 'r+') as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                data = json.load(f)
                data.pop(used_usb)
                data['old_usb'].remove(used_usb)
                f.seek(0)
                f.truncate()
                json.dump(data, f)
                f.flush()
                fcntl.flock(f, fcntl.LOCK_UN)
                break


factory = protocol.Factory()
factory.protocol = TSServProtocol
print 'waiting for connecting...'
reactor.listenTCP(PORT, factory)
reactor.run()