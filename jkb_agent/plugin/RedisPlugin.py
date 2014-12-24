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
Jiankongbao redis plugin
author@huohuiliang
"""


import time
from lib import jkbLib
import traceback

import  codecs

from p_class import plugins

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

try:
    import json
except ImportError:
    import simplejson as json


class RedisPlugin(plugins.plugin):

    def __init__(self,taskId,taskConf,agentType,pluginId):
        plugins.plugin.__init__(self,taskId,taskConf,agentType,pluginId)


    def setData(self,data):
        try:
            self.lock.acquire()
            self.DataList.append(data)
        finally:
            self.lock.release()

    def data_format_MB(self, data):
        data = int(data)
        data = data/1048576
        data="%.2f" % data
        data = float(data)
        return data

    def data_format_Ratio(self, hit, mis):
        hit = int(hit)
        mis = int(mis)
        if (hit+mis) == 0 :
            return 0
        data = (hit*100)/(hit+mis)
        data = "%.2f" % data
        data = float(data)
        return data

    def getData(self):

        status_content = {}
        try:
            url=self.taskConf['statusUrl']
            url=url.replace('\/', "/")
            res = urllib2.urlopen(urllib2.Request(url))
            status_content = res.read()
            res.close()
            try:
                status_content = status_content.decode('UTF8')
            except Exception :
                status_content = status_content.decode('GBK')
            status_content = status_content.replace(codecs.BOM_UTF8.decode("UTF8"),"")
            status_content = json.loads(status_content)
            status_content['used_memory']=self.data_format_MB(status_content['used_memory'])
            status_content['keyspace_ratio']=self.data_format_Ratio(status_content['keyspace_hits'],status_content['keyspace_misses'])
            
            self.intStatus()
            
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
            
        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':status_content, 'error_info':self.error_info})
