from twisted.internet.protocol import Protocol, ClientFactory
from sys import stdout
from dloader_logger import logger
import traceback
import subprocess
import os
import sys
import time
from twisted.internet import reactor

DLOADER_PATH = '/home/apuser/lavatest/DLoader_R1.18.0601/Bin/sprd_dloader/DLoader'
#DLOADER_PATH = '/home/local/SPREADTRUM/pl.dong/work_dong/LAVA/for_dloader/lavatest/DLoader_R1.18.0601/Bin/sprd_dloader/DLoader'
#if there are some serial board on the worker, your need get the number of these boaders's count, and set it to SERIAL_PORT_COUNT
SERIAL_PORT_COUNT = 0
USB_INFO = '/home/apuser/lavatest/USBPortInfos.json'
THIS_USB = ''

def dloader(pac, ttyusbx):
    logger.info('fun dloader')
    # pro = subprocess.Popen(['sudo', DLOADER_PATH, '-pac', pac, '-dev', ttyusbx, '-reset'])
    pro = subprocess.Popen(['python', 'test.py'])
    # pro = subprocess.Popen(['sleep', '10'])
    return pro
    # os.system('sudo '+ DLOADER_PATH+ ' -pac '+ pac+ ' -dev '+ ttyusbx+' -reset')
    # reactor.stop()

# def enter_autodloader(sn):
#     logger.info('fun enter dloader: '+str(sn))
#     os.system('adb -s ' + sn + 'reboot autodloader')

# class Echo(Protocol):
#     def dataReceived(self, data):
#         ttyUSBX = data
#         if ttyUSBX == 'time_out':
#             print 'fail'
#             reactor.stop()
#         pac = sys.argv[1]
#         # serial_number = sys.argv[2]
#         # enter_autodloader(serial_number)
#         logger.info('ECHO pac '+pac)
#         print data
#         p = dloader(pac, ttyUSBX)
#         self.transport.write(str(p.pid).encode('utf-8'))
#
#         print 'transport finshed:', str(p.pid)
#         p.wait()
#         reactor.stop()
#         #stdout.write(data)


# class EchoClientFactory(ClientFactory):
#     def startedConnecting(self, connector):
#         print 'Started to connect.'
#         logger.info('Started to connect.')
#
#     def buildProtocol(self, addr):
#         print 'Connected.'
#         logger.info('Connected.')
#         return Echo()
#
#     def clientConnectionLost(self, connector, reason):
#         print 'Lost connection. Reason:', reason
#         logger.info('Lost connection. Reason: ' +str(reason))
#
#     def clientConnectionFailed(self, connector, reason):
#         print 'Connection failed. Reason:', reason
#         logger.info('Connection failed.  Reason: ' +str(reason))


class TSClntProtocol(Protocol):
    # def sendData(self):
    #     data = raw_input("> ")
    #     if data:
    #         print '...sending %s...' % data
    #         self.transport.write(data)
    #     else:
    #         self.transport.loseConnection()
    #
    # def connectionMade(self):
    #     self.sendData()

    def dataReceived(self, data):
        ttyUSBX = data
        if ttyUSBX == 'time_out':
            print 'fail'
            reactor.stop()
        pac = sys.argv[1]
        # serial_number = sys.argv[2]
        # enter_autodloader(serial_number)
        logger.info('ECHO pac ' + pac)
        print data
        p = dloader(pac, ttyUSBX)
        print os.getpgid(p.pid)
        pgid = os.getpgid(p.pid)
        self.transport.write('-'+str(pgid).encode('utf-8'))
        self.transport.doWrite()

        print 'transport finshed:', str(p.pid)
        p.wait()
        # reactor.stop()
        self.transport.loseConnection()

class TSClntFactory(ClientFactory):
    protocol = TSClntProtocol
    clientConnectionLost = clientConnectionFailed = lambda self, connector, reason: reactor.stop()

if __name__ == '__main__':

    try:
        reactor.connectTCP('localhost', 21567, TSClntFactory())
        reactor.run()
    except:
        logger.info(traceback.format_exc())
