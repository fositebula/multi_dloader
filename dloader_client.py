from twisted.internet.protocol import Protocol, ClientFactory
from sys import stdout
from dloader_logger import logger
import traceback
import subprocess
import sys
from twisted.internet import reactor

DLOADER_PATH = '/home/apuser/lavatest/DLoader_R1.18.0601/Bin/sprd_dloader/DLoader'
#DLOADER_PATH = '/home/local/SPREADTRUM/pl.dong/work_dong/LAVA/for_dloader/lavatest/DLoader_R1.18.0601/Bin/sprd_dloader/DLoader'
#if there are some serial board on the worker, your need get the number of these boaders's count, and set it to SERIAL_PORT_COUNT
SERIAL_PORT_COUNT = 0
USB_INFO = '/home/apuser/lavatest/USBPortInfos.json'
THIS_USB = ''

def dloader(pac, ttyusbx):
    pro = subprocess.run(['sudo', DLOADER_PATH, '-pac', pac, '-dev', ttyusbx, '-reset'])
    #os.system('sudo '+ DLOADER_PATH+ ' -pac '+ pac+ ' -dev '+ ttyusbx+' -reset')

class Echo(Protocol):
    def dataReceived(self, data):
        ttyUSBX = data
        pac = sys.argv[1]
        dloader(pac, ttyUSBX)
        stdout.write(data)


class EchoClientFactory(ClientFactory):
    def startedConnecting(self, connector):
        print 'Started to connect.'
        logger.info('Started to connect.')

    def buildProtocol(self, addr):
        print 'Connected.'
        logger.info('Connected.')
        return Echo()

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection. Reason:', reason
        logger.info('Lost connection. Reason: ' +str(reason))

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason
        logger.info('Connection failed.  Reason: ' +str(reason))

try:
    reactor.connectTCP('localhost', 21567, EchoClientFactory())
    reactor.run()
except:
    logger.info(traceback.format_exc())