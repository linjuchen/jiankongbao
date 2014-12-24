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
Jiankongbao nginx plugin
author@huohuiliang
"""


import time
from lib import jkbLib
import traceback

import re

from p_class import plugins

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
import  codecs

class NginxPlugin(plugins.plugin):

    def __init__(self,taskId,taskConf,agentType,pluginId):
        plugins.plugin.__init__(self,taskId,taskConf,agentType,pluginId)


    def setData(self,data):
        try:
            self.lock.acquire()
            self.DataList.append(data)
        finally:
            self.lock.release()

        
    def getData(self):
        redata={}
        try:
            url=self.taskConf['statusUrl']
            url=url.replace('\/', "/")
            res = urllib2.urlopen(urllib2.Request(url))
            data = res.read()
            res.close()
            try:
                data = data.decode("UTF8")
            except Exception :
                data = data.decode("GBK")
            data = data.replace(codecs.BOM_UTF8.decode("UTF8"),"")
            rem = re.compile(r'Active connections: ([0-9]*)',re.M)
            matches = rem.findall(data)
            if matches :
                curr_reqs = matches[0]
            else :
                jkbLib.error(self.logHead + ' data format:Active connections')
                return False
                
            rem = re.compile(r' ([0-9]*) ([0-9]*) ([0-9]*) ',re.M)
            matches = rem.findall(data)
            if matches :
                accepts = matches[0][0]
                handled = matches[0][1]
                requests = matches[0][2]
            else :
                jkbLib.error(self.logHead + ' data format:num')
                return False
                
            rem = re.compile(r'Reading: ([0-9]*)',re.M)
            matches = rem.findall(data)
            if matches :
                reading = matches[0]
            else :
                jkbLib.error(self.logHead + ' data format:Reading')
                return False
                
            rem = re.compile(r'Writing: ([0-9]*)',re.M)
            matches = rem.findall(data)
            if matches :
                writing = matches[0]
            else :
                jkbLib.error(self.logHead + ' data format:Writing')
                return False
                
            rem = re.compile(r'Waiting: ([0-9]*)',re.M)
            matches = rem.findall(data)
            if matches :
                waiting = matches[0]
            else :
                jkbLib.error(self.logHead + ' data format:Waiting')
                return False
                
            redata={'curr_reqs':curr_reqs, 'reading':reading, 'writing':writing,
                     'waiting':waiting, 'accepts':accepts, 'handled':handled, 'requests':requests}
                     
            self.intStatus()
 

        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())

        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':redata, 'error_info':self.error_info})



