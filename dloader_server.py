# coding=utf-8
import time
from twisted.internet import protocol, reactor
import json
import os
import fcntl
class NoUSBInfoConfig(Exception):
    pass


CONF_FILE = 'USBPortInfo.json'
PORT = 21567

class TSServProtocol(protocol.Protocol):

    def connectionMade(self):

        clnt = self.clnt = self.transport.getPeer().port
        print '...conneting from:', clnt

        if not os.path.exists(CONF_FILE):
            raise NoUSBInfoConfig('There is no '+CONF_FILE)

        dev_usbs = filter(lambda x: 'ttyUSB' in x, os.listdir('/dev/'))

        _flag = False
        with open(CONF_FILE, 'r+') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            data = json.load(f)
            lava_used = []
            #收集哪些是lava用的端口
            for k, v in data.iteritems():
                if data[k]['who'] != 0:
                    lava_used.append(k)

            #将不是lava用的找出来
            lava_not_used = set(dev_usbs) - (lava_used)

            #把不是lava用的更新到USB info文件中
            for u in lava_not_used:
                data[u] = {'used':True, 'who':0}
            #从已用的usb中找到中间没有用的usb口,因为中间的口可能有空闲的
            for i in range(dev_usbs[-1][-1]):
                checking_usb = 'ttyUSB'+str(i)
                if checking_usb in dev_usbs:
                    continue
                _flag = True
                data[checking_usb] = {'used':True, 'who':clnt}
                self.transport.write(checking_usb.encode('utf-8'))
                break
            #如果从已有的口中找不到就生成一个新的
            if not _flag:
                new_usb = 'ttyUSB'+str(int(dev_usbs[-1][-1]) + 1)
                data[new_usb] = {'used':True, 'who':clnt}
            #将最新的数据更新到文件中
            f.seek(0)
            f.truncate()
            json.dump(data, f)

            fcntl.flock(f, fcntl.LOCK_UN)

    def connectionLost(self, reason):
        clnt = self.clnt = self.transport.getPeer().port
        print 'lost client '+str(clnt)

        used_usb = ''
        with open(CONF_FILE, 'r+') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            data = json.load(f)
            for k, v in data.iteritems():
                if str(v['who']) == str(clnt):
                    used_usb = k
                    # v['who'] = 0
                    # v['used'] = False
                    # f.seek(0)
                    # f.truncate()
                    # json.dump(data, f)
                    # f.flush()
                    # self.transport.write(k.encode('utf-8'))
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
                data[used_usb]['who'] = 0
                data[used_usb]['used'] = False
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