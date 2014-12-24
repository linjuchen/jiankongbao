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
Jiankongbao memcache plugin
author@huohuiliang
"""


import time
from lib import jkbLib
import traceback

from p_class import plugins

import  codecs

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

try:
    import json
except ImportError:
    import simplejson as json


class MemcachePlugin(plugins.plugin):

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
        data="%.2f" % data
        data = float(data)
        return data
    
    def getData(self):
        status_content = {}
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
            status_content = json.loads(data)
            status_content['bytes']=self.data_format_MB(status_content['bytes'])
            status_content['limit_maxbytes']=self.data_format_MB(status_content['limit_maxbytes'])
            status_content['keyspace_ratio']=self.data_format_Ratio(status_content['get_hits'],status_content['get_misses'])
            
            self.intStatus()
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())

        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':status_content, 'error_info':self.error_info})



