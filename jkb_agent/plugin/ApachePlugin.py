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
Jiankongbao apache plugin
author@huohuiliang
"""


import time
from lib import jkbLib

import traceback

from p_class import plugins

import re

import  codecs

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2


class ApachePlugin(plugins.plugin):

    def __init__(self,taskId,taskConf,agentType,pluginId):
        plugins.plugin.__init__(self,taskId,taskConf,agentType,pluginId)


    def setData(self,data):
        try:
            self.lock.acquire()
            self.DataList.append(data)
        finally:
            self.lock.release()

    def strtotime(self, strtime):
        try:
            time_tuple = time.strptime(strtime, "%d-%b-%Y %H:%M:%S")
            timestamp = time.mktime(time_tuple)
            return timestamp
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            return False

        
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
            rem = re.compile(r'<dt>Current Time: [a-zA-Z]*, (.*) [^0-9]*</dt>',re.M)
            matches = rem.findall(data)
            if matches :
                curr_time = self.strtotime(matches[0])
            else :
                jkbLib.error(self.logHead + ' data format:Current Time')
                return False
            
            rem = re.compile(r'<dt>Restart Time: [a-zA-Z]*, (.*) [^0-9]*</dt>',re.M)
            matches = rem.findall(data)
            if matches :
                restart_time = self.strtotime(matches[0])
            else :
                jkbLib.error(self.logHead + ' data format:Restart Time')
                return False
            uptime = curr_time - restart_time;
            
            rem = re.compile(r'([0-9]*) requests currently being processed',re.M)
            matches = rem.findall(data)
            if matches :
                curr_reqs =  matches[0]
            else :
                jkbLib.error(self.logHead + ' data format:requests currently')
                return False
            
            rem = re.compile(r'<dt>Total accesses: ([0-9]*) -',re.M)
            matches = rem.findall(data)
            if matches :
                total_reqs =  matches[0]
            else :
                jkbLib.error(self.logHead + ' data format:Total accesses')
                return False
            
            
            rem = re.compile(r'<pre>(.*)</pre>',re.S)
            matches = rem.findall(data)
            if matches :
                statusStr = matches[0]
            else :
                jkbLib.error(self.logHead + ' data format:pre')
                return False
            
            lens = len(statusStr)
            curr_reqs_status = {}
            for i in range(0, lens) :
                tmp = statusStr[i]
                if tmp ==  "\n" :
                    continue
                if tmp in curr_reqs_status :
                    curr_reqs_status[tmp] += 1
                else :
                    curr_reqs_status[tmp] = 1
                
            redata = {'uptime':uptime, 'total_reqs':total_reqs, 'curr_reqs':curr_reqs, 'curr_reqs_status':curr_reqs_status}
            
            self.intStatus()
 
        except Exception :
            jkbLib.error(self.logHead+traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
            
        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':redata, 'error_info':self.error_info})
