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
Jiankongbao tcp plugin
author@huohuiliang
"""
import socket
import math
import random
import time
from lib import jkbLib

import traceback

from p_class import plugins



class TcpPlugin(plugins.plugin):

    def __init__(self,taskId,taskConf,agentType,pluginId):
        plugins.plugin.__init__(self,taskId,taskConf,agentType,pluginId)


    def setData(self,data):
        try:
            self.lock.acquire()
            self.DataList.append(data)
        finally:
            self.lock.release()

    def microtime(self, get_as_float = True) :
        if get_as_float:
            return time.time()
        else:
            return '%f %d' % math.modf(time.time())

    def getData(self):
        redata={}
        try:
            host=self.taskConf['host']
            host=host.replace('\/', "/")
            port = self.taskConf['port']
            
            ConTime=5
            NORMAL=0
            Refused =10061
            Timeout=10060
            
            resp_result = '1'
            resp_status = ''
            resp_info={}
            resp_err = '0'
            
            dns_resolve_start_time = self.microtime()
            hostInfo=''
            hostInfo = socket.gethostbyname_ex(host)
            dns_resolve_end_time = self.microtime()
            dns_resolve_time_be = (dns_resolve_end_time - dns_resolve_start_time)*1000
            dns_resolve_time = '%.3f' % dns_resolve_time_be
            resp_info['namelookup_time'] = dns_resolve_time
            url_ip = ''
            if hostInfo[2]:
                lens = len(hostInfo[2])
                IP_key = random.randint(0, lens)
                IP_key = IP_key - 1
                url_ip = hostInfo[2][IP_key]
            else:
                resp_result = '0'
                resp_status = 'TCP_RESOLVE_ERROR'
            resp_info['ip'] = url_ip
            
            start_time = self.microtime()
            cs=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            address=(str(url_ip),int(port))
            status = cs.connect_ex((address))
            cs.setblocking(0)
            cs.settimeout(ConTime)
            end_time = self.microtime()
            connect_time_be = (end_time - start_time)*1000
            connect_time = '%.3f' % connect_time_be
            resp_info['connect_time'] = connect_time
            
            status=int(status)
            if status == NORMAL :  
                resp_status = 'TCP_CONNECT_OK'
            elif status==Refused:
                resp_result = '0'
                resp_status = 'TCP_CONNECT_REFUSED'
            elif status == Timeout:
                resp_result = '0'
                resp_status = 'TCP_CONNECT_TIMEOUT'
            else:
                resp_result = '0'
                resp_status = 'TCP_CONNECT_ERROR'
            
            resp_info['errno']=''
            resp_info['errmsg']=''
            total_time=connect_time_be+dns_resolve_time_be
            total_time = '%.3f' % total_time
            resp_info['total_time'] = total_time
    
            redata = {'resp_result':resp_result, 'resp_status':resp_status, 
            'resp_time':total_time, 'resp_err':resp_err, 'extend':resp_info}
            
            self.intStatus()
 
        except Exception :
            jkbLib.error(self.logHead+traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
            
        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':redata, 'error_info':self.error_info})
