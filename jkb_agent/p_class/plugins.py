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
Jiankongbao  plugin class
author@huohuiliang
"""

import random
import time
from lib import jkbLib
import threading

from config import jkbConfig
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
try:
    from  urllib import parse
except ImportError:
    import urllib as parse

try:
    import json
except ImportError:
    import simplejson as json
    
try:
    import zlib
except ImportError:
    zlib=''
    
try:
    import base64
except ImportError:
    base64=''
    
import traceback

import re


class plugin(threading.Thread):

    def __init__(self,taskId,taskConf,agentType,pluginId):
        self.taskId = taskId
        self.taskConf = taskConf
        self.taskConf_tmp = taskConf
        self.agentType = agentType
        self.pluginId = pluginId
        self.logHead = 'relation_id:'+taskId+'  type:'+agentType+'  error:'
        self.code = 'A001'
        self.error_info = ''
        self.error_time = 0
        self.lock = threading.Lock()
        self.running=True
        self.interval=300
        self.DataList=[]
        self.ser_time=0
        threading.Thread.__init__(self)

    def run(self):
        self.taskConf = self.taskConf_tmp
        if 'ser_time' in self.taskConf:
            self.ser_time=int(self.taskConf['ser_time']-time.time())
        time.sleep(random.randint(3, 50))
        while self.running:
            self.taskConf = self.taskConf_tmp
            if 'pluginTime' in self.taskConf:
                self.interval=self.taskConf['pluginTime']
            cur_time = time.time()           
            self.getData()
            self.postData()
            cur_time = time.time() - cur_time
            #cur_time = int(cur_time)
            if((cur_time+10) < self.interval) :
                time.sleep(self.interval - cur_time)
            else :
                jkbLib.error('get data out time!!')
                time.sleep(60)
           
            
    def setIntervalTime(self,int_time):
        try:
            self.lock.acquire()
            self.interval=int_time
        finally:
            self.lock.release()
    
    def setConf(self, conf):
        try:
            self.lock.acquire()
            self.taskConf_tmp = conf
        finally:
            self.lock.release()

    def getCurTime(self):
        try:
            self.lock.acquire()
            return int(time.time()+self.ser_time)
        finally:
            self.lock.release()

    def returnData(self):
        try:
            self.lock.acquire()
            return self.DataList
        finally:
            self.lock.release()
    
    def clearData(self):
        try:
            self.lock.acquire()
            self.DataList=[]
        finally:
            self.lock.release()

    def plugStop(self):
        try:
            self.lock.acquire()
            self.running=False
        finally:
            self.lock.release()
        

    def plugStart(self):
        try:
            self.lock.acquire()
            self.running=True
        finally:
            self.lock.release()
    
    def errorInfoDone(self, info):
        try:
            self.lock.acquire()
            rem = re.compile(r'(.*)\n',re.M)
            matches = rem.findall(info)
            lens=len(matches)
            self.error_time+=1
            if lens>1:
                self.error_info = matches[0]+matches[1]+'  '+matches[lens-1]
            else :
                self.error_info = info
            self.code='A002'
            if self.error_time>10:
                self.code='A003'
        finally:
            self.lock.release()

    def intStatus(self):
        self.code = 'A001'
        self.error_time = 0
        self.error_info = ''

    def postData(self):
        try:
            reData={}
            reData[self.taskId+''] = self.returnData()
            self.clearData()
            try:
                reData = json.dumps(reData,ensure_ascii=False)
            except Exception:
                jkbLib.error('json.dumps loss!')
                jkbLib.error(traceback.format_exc())
            if zlib:
                reData = reData.encode('UTF8') 
                reData = zlib.compress(reData, 9)
                if base64:
                    reData = base64.encodestring(reData)
                else:
                    reData = reData.encode('base64')
            parms = {'data':reData,'post_time':'','plug_post':'true'}
            parms = parse.urlencode(parms)
            parms=parms.encode('UTF8') 
            try:
                res =  urllib2.urlopen(urllib2.Request(jkbConfig.postUrl , parms))
                command = res.read()
                res.close()
            except Exception:
                jkbLib.error(traceback.format_exc())
                res =  urllib2.urlopen(urllib2.Request(jkbConfig.postUrl , parms))
                command = res.read()
                res.close()
        except Exception:
            jkbLib.error(traceback.format_exc())
