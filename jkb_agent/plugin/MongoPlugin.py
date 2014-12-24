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
Jiankongbao mongodb plugin
author@huohuiliang
"""


import time
from lib import jkbLib

import traceback

from p_class import plugins

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
import  codecs

try:
    import json
except ImportError:
    import simplejson as json


class MongoPlugin(plugins.plugin):

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
            data = json.loads(data)

            if 'serverStatus' not in data :
                jkbLib.error(self.logHead + ' data format:serverStatus')
                return False
            redata['version']=data['serverStatus']['version']
            redata['host']=data['serverStatus']['host']
            redata['uptime']=data['serverStatus']['uptime']
            if 'ratio' not in data['serverStatus']['globalLock']:
                data['serverStatus']['globalLock']['ratio']=0
            redata['globalLock_ratio']=data['serverStatus']['globalLock']['ratio']
            redata['connections_current']=data['serverStatus']['connections']['current']
            redata['connections_available']=data['serverStatus']['connections']['available']
            redata['page_faults']=data['serverStatus']['extra_info']['page_faults']
            redata['globalLock_currentQueue_total']=data['serverStatus']['globalLock']['currentQueue']['total']
            redata['globalLock_currentQueue_readers']=data['serverStatus']['globalLock']['currentQueue']['readers']
            redata['globalLock_currentQueue_writers']=data['serverStatus']['globalLock']['currentQueue']['writers']
            redata['opcounters_insert']=data['serverStatus']['opcounters']['insert']
            redata['opcounters_query']=data['serverStatus']['opcounters']['query']
            redata['opcounters_update']=data['serverStatus']['opcounters']['update']
            redata['opcounters_delete']=data['serverStatus']['opcounters']['delete']
            redata['opcounters_getmore']=data['serverStatus']['opcounters']['getmore']
            redata['opcounters_command']=data['serverStatus']['opcounters']['command']
            redata['mem_resident']=data['serverStatus']['mem']['resident']
            redata['mem_maped']=data['serverStatus']['mem']['mapped']
            redata['indexCounters_btree_accesses']=data['serverStatus']['indexCounters']['btree']['accesses']
            
            self.intStatus()
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())

        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':redata, 'error_info':self.error_info})



