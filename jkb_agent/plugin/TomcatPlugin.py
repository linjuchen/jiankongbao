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
Jiankongbao tomcat plugin
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



class TomcatPlugin(plugins.plugin):

    def __init__(self,taskId,taskConf,agentType,pluginId):
        plugins.plugin.__init__(self,taskId,taskConf,agentType,pluginId)


    def setData(self,data):
        try:
            self.lock.acquire()
            self.DataList.append(data)
        finally:
            self.lock.release()
    
    def getTomcatData(self):
        status_content = {}
        try:
            url=self.taskConf['statusUrl']
            url=url.replace('\/', "/")
            
            username = self.taskConf['user']
            password = self.taskConf['password']
            appname = self.taskConf['appname']

            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None,url,username,password)
            handler = urllib2.HTTPBasicAuthHandler(password_mgr)
            opener = urllib2.build_opener(handler)
            urllib2.install_opener(opener)
            resp = urllib2.urlopen(urllib2.Request(url))
            data=resp.read() 
            resp.close()
            try:
                data = data.decode("UTF8")
            except Exception :
                data = data.decode("GBK")
            
            rem = re.compile(r'<td class="row-center"><small>(.*)</small></td>',re.M)
            matches = rem.findall(data)
            if matches :
                status_content['tomcat_ver'] = matches[0]
                status_content['jvm_ver'] = matches[1]
                status_content['os_ver'] = matches[3]+'  '+matches[4]
            else :
                jkbLib.error(self.logHead +"can't match the data tomcat_ver")
                self.errorInfoDone("can't match the data tomcat_ver")
                return False
                
            rem = re.compile(r'Free memory: ([0-9.]*) MB Total memory: ([0-9.]*) MB Max memory: ([0-9.]*) MB</p>',re.M)
            matches = rem.findall(data)
            if matches :
                status_content['free_memory'] = matches[0][0]
                status_content['total_memory'] = matches[0][1]
                status_content['max_memory'] = matches[0][2]
            else :
                jkbLib.error(self.logHead +"can't match the data free_memory")
                self.errorInfoDone("can't match the data free_memory")
                return False 
                
            rem = re.compile(r'<h1>([^JVM][^</.]*)</h1>',re.M)
            matches = rem.findall(data)
            flag=-1
            if matches :
                for key, val in enumerate(matches):
                    val=val.strip('"')
                    if val == appname:
                        flag=key
                        break
                if flag == -1:
                    jkbLib.error(self.logHead +"can't find the data appname")
                    self.errorInfoDone("can't find the data appname")
                    return False
            else:
                jkbLib.error(self.logHead +"can't match the data appname")
                self.errorInfoDone("can't match the data appname")
                return False
            status_content['appname']=appname
            rem = re.compile(r'Max threads: ([0-9]*)[^\d^.]',re.M)
            matches = rem.findall(data)
            if matches :
                status_content['max_threads'] = matches[flag]
            else:
                jkbLib.error(self.logHead +"can't match the data max_threads")
                self.errorInfoDone("can't match the data max_threads")
                return False
            
            rem = re.compile(r'Current thread count: ([0-9]*)[^\d^.]',re.M)
            matches = rem.findall(data)
            if matches :
                status_content['cur_thread'] = matches[flag]
            else:
                jkbLib.error(self.logHead +"can't match the data cur_thread")
                self.errorInfoDone("can't match the data cur_thread")
                return False
                
            rem = re.compile(r'Current thread busy: ([0-9]*)[^\d^.]',re.M)
            matches = rem.findall(data)
            if matches :
                status_content['cur_thread_b'] = matches[flag]
            else:
                jkbLib.error(self.logHead +"can't match the data cur_thread_b")
                self.errorInfoDone("can't match the data cur_thread_b")
                return False
                
            rem = re.compile(r'Max processing time: ([0-9.]*)[^\d^.]',re.M)
            matches = rem.findall(data)
            if matches :
                status_content['max_processing_time'] = matches[flag]
            else:
                jkbLib.error(self.logHead +"can't match the data max_processing_time")
                self.errorInfoDone("can't match the data max_processing_time")
                return False
                
            rem = re.compile(r'Processing time: ([0-9.]*)[^\d^.]',re.M)
            matches = rem.findall(data)
            if matches :
                status_content['processing_time'] = matches[flag]
            else:
                jkbLib.error(self.logHead +"can't match the data processing_time")
                self.errorInfoDone("can't match the data processing_time")
                return False
            
            rem = re.compile(r'Request count: ([0-9.]*)[^\d^.]',re.M)
            matches = rem.findall(data)
            if matches :
                status_content['request_count'] = matches[flag]
            else:
                jkbLib.error(self.logHead +"can't match the data request_count")
                self.errorInfoDone("can't match the data request_count")
                return False
                
            rem = re.compile(r'Error count: ([0-9.]*)[^\d^.]',re.M)
            matches = rem.findall(data)
            if matches :
                status_content['error_count'] = matches[flag]
            else:
                jkbLib.error(self.logHead +"can't match the data error_count")
                self.errorInfoDone("can't match the data error_count")
                return False
                
            rem = re.compile(r'Bytes received: ([0-9.]*)[^\d^.]',re.M)
            matches = rem.findall(data)
            if matches :
                status_content['bytes_received'] = matches[flag]
            else:
                jkbLib.error(self.logHead +"can't match the data bytes_received")
                self.errorInfoDone("can't match the data bytes_received")
                return False
                
            rem = re.compile(r'Bytes sent: ([0-9.]*)[^\d^.]',re.M)
            matches = rem.findall(data)
            if matches :
                status_content['bytes_sent'] = matches[flag]
            else:
                jkbLib.error(self.logHead +"can't match the data bytes_sent")
                self.errorInfoDone("can't match the data bytes_sent")
                return False
                
            self.intStatus()
            return status_content
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
            return False

    def getData(self):
        status_content = {}
        status_content=self.getTomcatData()
        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':status_content, 'error_info':self.error_info})
        


