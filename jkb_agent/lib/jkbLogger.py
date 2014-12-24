# -*- coding: utf-8 -*-
"""
 Copyright © 2012 云智慧（北京）科技有限公司 <http://www.jiankongbao.com/>
 
 Permission is hereby granted, free of charge, to any person obtaining a copy of this software
 and associated documentation files (the "Software"), to deal in the Software without restriction,
 including without limitation the rights to use, copy, modify, merge, publish, distribute,
 sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 
 The above copyright notice and this permission notice shall be included in all copies or
 substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
 BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
 DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
"""
"""
Jiankongbao logger
author@huohuiliang
"""

from config import jkbConfig

import time
import datetime

import platform
import traceback
import urllib
try:
    from  urllib import parse
except ImportError:
    import urllib as parse

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
try:
    import queue as Queue
except ImportError:
    import Queue
import threading
import logging
import logging.handlers
from lib import jkbLib




class LogSendThread(threading.Thread):

    def __init__(self, logQueue):

        self.logQueue = logQueue
        self.pythonVersion = platform.python_version()
        self.logUrl = jkbConfig.logUrl % {'key':jkbConfig.jkbKey}

        try:
            self.hostname = platform.uname()[1]
        except:
            self.hostname = 'Unknown'

        threading.Thread.__init__(self)

    def run(self):
        while True:
            try:
                items = []
                time.sleep(5)
                try:
                    while not self.logQueue.empty():
                        obj = self.logQueue.get()
                        if obj is None:
                            continue

                        item = {}
                        item['hostname'] = self.hostname
                        item['pythonVersion'] = self.pythonVersion

                        item['msg'] = obj.msg

                        item['filename'] = obj.filename
                        item['lineno'] = obj.lineno

                        item['levelname'] = obj.levelname
                        item['process'] = obj.process
                        item['threadName'] = obj.threadName

                        try:
                            item['funcName'] = obj.funcName
                        except:
                            pass

                        items.append(item)

                except Queue.Empty:
                    pass

                if len(items) == 0:
                    continue

                res = None
                try:
                    parms={'items':items}
                    parms=parse.urlencode(parms)
                    parms=parms.encode('UTF8')  
                    res = urllib2.urlopen(urllib2.Request(self.logUrl , parms))
                    res.read()
                finally:
                    if res is not None:
                        res.close()

            except Exception :
                print(traceback.format_exc())

class JkbHandler(logging.Handler):

    def __init__(self):
        logging.Handler.__init__(self)
        self.logQueue = Queue.Queue(0)
        self.logSend = LogSendThread(self.logQueue)
        self.logSend.setName('LogSend')
        self.logSend.start()

    def emit(self, record):
        try:
            if record is not None:
                self.logQueue.put_nowait(record)
        except Exception :
            print(traceback.format_exc())


def date(unixtime, format = '%m/%d/%Y %H:%M'):
    d = datetime.datetime.fromtimestamp(unixtime)
    return d.strftime(format)

def getLogger():

    logger = logging.getLogger('JKB')

    FileHandler = logging.FileHandler(jkbLib.getPath()+'log/'+date(time.time(), format = '%Y-%m-%d')+'.log')
    FileHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(FileHandler)

    #streamHandler = logging.StreamHandler()
    #streamHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    #logger.addHandler(streamHandler)

    #logging.handlers.JkbHandler = JkbHandler
    #logger.addHandler(logging.handlers.JkbHandler())

    logger.setLevel(logging.INFO)
    return logger
