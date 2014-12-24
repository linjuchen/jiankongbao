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
Jiankongbao ping plugin
author@huohuiliang
"""

import time
from lib import jkbLib
import traceback
import re
import subprocess
from p_class import plugins


class PingPlugin(plugins.plugin):

    def __init__(self,taskId,taskConf,agentType,pluginId):
        plugins.plugin.__init__(self,taskId,taskConf,agentType,pluginId)
        self.sys_type=jkbLib.UsePlatform()


    def setData(self,data):
        try:
            self.lock.acquire()
            self.DataList.append(data)
        finally:
            self.lock.release()
            
    def UTFdata(self, data):
        extend={}
        resp_time=-1
        try:
            rem = re.compile(r' \(([0-9.]*)\) ',re.M)
            matches = rem.findall(data)
            if matches:
                extend['target_ip']=matches[0]
            
            rem = re.compile(r'= [0-9.]*/([0-9.]*)/',re.M)
            matches = rem.findall(data)
            if matches:
                resp_time=matches[0]
        
            rem = re.compile(r'([0-9]+) bytes',re.M)
            matches = rem.findall(data)
            if matches:
                extend['bytes_per_request']=int(matches[0])
                extend['bytes_total']=int(matches[0])*3
            
            rem = re.compile(r'ttl=([0-9]*)',re.M)
            matches = rem.findall(data)
            if matches:
                extend['ttl']=int(matches[0])
            
            rem = re.compile(r'([0-9]*) packets transmitted, ([0-9]*) received, ([0-9]*)% packet loss',re.M)
            matches = rem.findall(data)
            if matches:
                extend['transmitted']=int(matches[0][0])
                extend['received']=int(matches[0][1])
                extend['loss']=int(matches[0][2])
            
            rem = re.compile(r'([^\n\r]+)',re.M)
            matches = rem.findall(data)
            if matches:
                extend['raw_data']=matches
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
            return False
        return {'extend':extend, 'resp_time':resp_time}

    def UTFWindowsdata(self, data):
        extend={}
        resp_time=-1
        try:
            rem = re.compile(r'([0-9.]*) with',re.M)
            matches = rem.findall(data)
            if matches:
                extend['target_ip']=matches[0]
            
            rem = re.compile(r'Average = ([0-9]*)ms',re.M)
            matches = rem.findall(data)
            if matches:
                resp_time=int(matches[0])
            
            rem = re.compile(r'with ([0-9]*) bytes',re.M)
            matches = rem.findall(data)
            if matches:
                extend['bytes_per_request']=int(matches[0])
                extend['bytes_total']=int(matches[0])*3
            
            rem = re.compile(r'TTL=([0-9]*)',re.M)
            matches = rem.findall(data)
            if matches:
                extend['ttl']=int(matches[0])
            
            rem = re.compile(r'Sent = ([0-9]*), Received = ([0-9]*), Lost = ([0-9]*) \(([0-9]*)% loss\)',re.M)
            matches = rem.findall(data)
            if matches:
                extend['transmitted']=int(matches[0][0])
                extend['received']=int(matches[0][1])
                extend['loss']=int(matches[0][3])
            
            rem = re.compile(r'([^\n\r]+)',re.M)
            matches = rem.findall(data)
            if matches:
                extend['raw_data']=matches
        except Exception :
            return False
        return {'extend':extend, 'resp_time':resp_time}

    def GBKdata(self, data):
        extend={}
        resp_time=-1
        try:
            import sys
            reload(sys)
            sys.setdefaultencoding('utf-8')
        except Exception :
            pass

        data_bytes=data.encode('GBK')

        try:
            rem = re.compile(r'\[([0-9.]*)\]',re.M)
            matches = rem.findall(data)
            if matches:
                extend['target_ip']=matches[0]
            
            rem = re.compile("平均 = ([0-9]*)ms".encode('GBK'),re.M)
            matches = rem.findall(data_bytes)
            if matches:
                resp_time=int(matches[0].decode('utf'))
            else:
                rem = re.compile(r'Average = ([0-9]*)ms',re.M)
                matches = rem.findall(data)
                if matches:
                    resp_time=int(matches[0])
                
            

            rem = re.compile("具有 ([0-9]*) 字节".encode('GBK'),re.M)
            matches = rem.findall(data_bytes)
            if matches:
                extend['bytes_per_request']=int(matches[0].decode('utf'))
                extend['bytes_total']=int(matches[0].decode('utf'))*3
            else:
                rem = re.compile(r'with ([0-9]*) bytes',re.M)
                matches = rem.findall(data)
                if matches:
                    extend['bytes_per_request']=int(matches[0])
                    extend['bytes_total']=int(matches[0])*3
            
            rem = re.compile(r'TTL=([0-9]*)',re.M)
            matches = rem.findall(data)
            if matches:
                extend['ttl']=int(matches[0])
            
            rem = re.compile("已发送 = ([0-9]*)，已接收 = ([0-9]*)，丢失 = ([0-9]*) \(([0-9]*)% 丢失\)".encode('GBK'),re.M)
            matches = rem.findall(data_bytes)
            if matches:
                extend['transmitted']=int(matches[0][0].decode('utf'))
                extend['received']=int(matches[0][1].decode('utf'))
                extend['loss']=int(matches[0][3].decode('utf'))
            else:
                rem = re.compile(r'Sent = ([0-9]*)，Received = ([0-9]*)，Lost = ([0-9]*) \(([0-9]*)% loss\)',re.M)
                matches = rem.findall(data)
                if matches:
                    extend['transmitted']=int(matches[0][0])
                    extend['received']=int(matches[0][1])
                    extend['loss']=int(matches[0][3])
            
            rem = re.compile(r'([^\n\r]+)',re.M)
            matches = rem.findall(data)
            if matches:
                extend['raw_data']=matches
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
            return False
        return {'extend':extend, 'resp_time':resp_time}

    def getPingData(self):
        host=self.taskConf['statusUrl']
        resp_data={}
        resp_result='1'
        resp_status = 'PING OK'
        resp_err = '0'
        resp_time = 0
        extend={}
        try :
            if self.sys_type == 'Windows':
                cmd='ping -n 3 '+host
            else:
                cmd='ping -c 3 '+host
            
            returnstr=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
            data = returnstr.stdout.read()
            error= returnstr.stderr.read()
            if error:
                jkbLib.error(self.logHead + error)
                self.errorInfoDone(error)
                return False
            
            try :
                data = data.decode('utf-8')
                if self.sys_type=='Windows':
                    data =self.UTFWindowsdata(data)
                else:
                    data =self.UTFdata(data)
            except Exception:
                data = data.decode('GBK')
                data =self.GBKdata(data)
            
            if data:
                resp_time=data['resp_time']
                extend=data['extend']
            else:
                jkbLib.error(self.logHead + ' data format:null')
                return False
            
            if 'loss' not in extend:
                resp_time = 0
                resp_result = '0'
                resp_status = 'PING_LOSS'
                resp_err = '1'
                extend['loss']=100
            elif resp_time == -1 or extend['loss']==100:
                resp_time = 0
                resp_result = '0'
                resp_status = 'PING_LOSS'
    
            self.intStatus()
            resp_data['resp_result']=resp_result
            resp_data['resp_status']=resp_status
            resp_data['resp_time']=resp_time
            resp_data['resp_err']=resp_err
            resp_data['extend']=extend
            return resp_data
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
            return False


    def getData(self):
        status_content = {}
        status_content=self.getPingData()
        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':status_content, 'error_info':self.error_info})

