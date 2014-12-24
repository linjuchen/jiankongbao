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
Jiankongbao lighttpd plugin
author@huohuiliang
"""


import time
from lib import jkbLib

import traceback

import re

import  codecs

from p_class import plugins

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2


class LighttpdPlugin(plugins.plugin):

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
            rem = re.compile(r'<h1>Server-Status(.*)<h2>Connections',re.S)
            matches = rem.findall(data)
            if matches :
                status_content = matches[0]
            else :
                jkbLib.error(self.logHead + ' data format:Server-Status')
                return False
           
            rem = re.compile(r'Requests<\/td><td class="string">([0-9 ]*)req\/s<\/td>',re.S)
            matches = rem.findall(status_content)
            if matches :
                rps = matches[1]
                rps = int(rps)
            else :
                jkbLib.error(self.logHead + ' data format:Requests')
                return False
            
            rem = re.compile(r'<b>([0-9 ]*)connections',re.S)
            matches = rem.findall(status_content)
            if matches :
                curr_reqs = matches[0]
                curr_reqs = int(curr_reqs)
            else :
                jkbLib.error(self.logHead + ' data format:connections')
                return False
            
            rem = re.compile(r'connections<\/b>(.*)<\/pre><hr',re.S)
            matches = rem.findall(status_content)
            if matches :
                statusStr = matches[0]
            else :
                jkbLib.error(self.logHead + ' data format:connections pre')
                return False
            lens = len(statusStr)
            curr_reqs_status={}
            for i in range(0, lens) :
                tmp = statusStr[i]
                if tmp ==  "\n" :
                    continue
                if tmp in curr_reqs_status :
                    curr_reqs_status[tmp] += 1
                else :
                    curr_reqs_status[tmp] = 1
            
            redata={'rps':rps, 'curr_reqs':curr_reqs, 'curr_reqs_status':curr_reqs_status}
            for key in curr_reqs_status :
                redata['s_'+key] = curr_reqs_status[key]
                
            self.intStatus()

        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())

        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':redata, 'error_info':self.error_info})

