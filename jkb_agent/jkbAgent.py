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
Jiankongbao Agent Process.
author@huohuiliang
"""


from config import jkbConfig
from lib import jkbLib

import os
import sys
import time
import socket
try:
    import zlib
except ImportError:
    zlib=''
try:
    import base64
except ImportError:
    base64=''

import threading
import traceback

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

#proxy
try:
    if jkbConfig.useProxy :
        proxy_handler = urllib2.ProxyHandler({'http': str(jkbConfig.proxy_host)+':'+str(jkbConfig.proxy_port)})
        proxy_opener = urllib2.build_opener(proxy_handler)
        urllib2.install_opener(proxy_opener)
except Exception :
    pass
    
#https
if jkbConfig.jkbServer[0:5] == 'https':
    import  ssl
    try :
        import httplib
    except ImportError:
        import http.client as httplib
    class HTTPSConnectionV3(httplib.HTTPSConnection):
        def __init__(self, *args, **kwargs):
            httplib.HTTPSConnection.__init__(self, *args, **kwargs)
             
        def connect(self):
            sock = socket.create_connection((self.host, self.port), self.timeout)
            if self._tunnel_host:
                self.sock = sock
                self._tunnel()
            try:
                self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv3)
            except ssl.SSLError:
                self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv23)
                 
    class HTTPSHandlerV3(urllib2.HTTPSHandler):
        def https_open(self, req):
            return self.do_open(HTTPSConnectionV3, req)
    # install opener
    urllib2.install_opener(urllib2.build_opener(HTTPSHandlerV3()))


class AgentProcess(threading.Thread):

    def __init__(self):
        self.running = True
        self.mac = jkbLib.get_mac_address()
        self.ip = jkbLib.get_ip()
        self.os_type = jkbLib.UsePlatform()
        self.plugConf = self.getUsrPluginSet()
        self.post_time = 0
        self.post_interval=180
        self.pluginTime=175
        threading.Thread.__init__(self)
        socket.setdefaulttimeout(30)
        
    def __del__(self):
        jkbLib.rmPid('agent')


    def stop(self):
        self.running = False
    
    def run(self):
        self.objList = {}
        try:
            if 'agent' in self.plugConf and 'agentTime' in self.plugConf['agent'] :
                self.post_interval = self.plugConf['agent']['agentTime']
                
            if 'agent' in self.plugConf and 'pluginTime' in self.plugConf['agent'] :
                self.pluginTime = self.plugConf['agent']['pluginTime']
                
            if 'agent' in self.plugConf and 'post_time' in self.plugConf['agent'] :
                self.post_time = self.plugConf['agent']['post_time']
            else :
                jkbLib.error('none set post time!')
            
            if 'error' in self.plugConf :
                jkbLib.error(self.plugConf['error'])
          
            if 'plugin' in self.plugConf :
                for taskId in self.plugConf['plugin']:
                    plug = self.plugConf['plugin'][taskId+'']
                    if plug['status'] == '1':
                        self.startOne(plug)
            else :
                jkbLib.info('none plugin info!!')
                
            cur_time = 0
            while self.running:
                if((cur_time+10) < self.post_interval) :
                    time.sleep(self.post_interval - cur_time)
                else :
                    jkbLib.error('post data out time!!')
                    time.sleep(180)
                cur_time = time.time()
                command = self.postData()
                self.doneCommand(command)
                cur_time = time.time() - cur_time
                #cur_time = int(cur_time)
        except Exception :
            jkbLib.error(traceback.format_exc())


    def doneCommand(self,command):
        if command == '':
            return False
        try:
            if 'agent' in command and 'post_time' in command['agent']:
                self.post_time = command['agent']['post_time']
            else :
                jkbLib.error('none return post_time!!')
                
            if 'agent' in command and 'agentTime' in command['agent'] :
                self.post_interval = command['agent']['agentTime']
                
            if 'error' in command :
                jkbLib.error(command['error'])
    
            if 'agent' in command and 'pluginTime' in command['agent'] and self.pluginTime != command['agent']['pluginTime'] :
                self.pluginTime = command['agent']['pluginTime']
                for pid in self.objList :
                    self.objList[pid].setIntervalTime(self.pluginTime)
     
            if 'sysCommand' in command  and  'agent' in command['sysCommand'] :
                if command['sysCommand']['agent'] == 'restart':
                    self.restart()
                if command['sysCommand']['agent'] == 'getlog':
                    self.postlog()
    
            if  'plugin' in command :
                for  plugOne in self.objList :
                    if plugOne not in command['plugin'] :
                        if  len(command['plugin'])==0:
                            command['plugin']={}
                        command['plugin'][plugOne]={'taskId':plugOne,'status':'0'}
                    else :
                        self.objList[plugOne].setConf(command['plugin'][plugOne]['taskConf'])
                
                for taskId in command['plugin']:
                    plug = command['plugin'][taskId+'']
                    if plug['status'] == '1' and plug['taskId'] not in self.objList :
                        self.startOne(plug)
                        
                    if plug['status'] == '0' and  plug['taskId']  in self.objList  :
                        self.stopOne(plug)
        except Exception :
            jkbLib.error(traceback.format_exc())


    def startOne(self,plug):
        try:
            self.initPlug(plug)
            module_meta = __import__('plugin', globals(), locals(), [str(plug['pluginFileName'])]) 
            class_meta = getattr(module_meta, plug['pluginFileName'])
            c = getattr(class_meta, plug['pluginClassName'])
            obj = c(plug['taskId'],plug['taskConf'],plug['agentType'],plug['pluginId'])
            self.objList[plug['taskId']]=obj
            obj.setIntervalTime(self.pluginTime)
            obj.setName(plug['pluginClassName']+plug['taskId'])
            obj.setDaemon(True)
            obj.start()
            
        except Exception :
            jkbLib.error(traceback.format_exc())
        

    def stopOne(self,plug):
        try:
            self.objList[plug['taskId']].plugStop()
            del self.objList[plug['taskId']]
        except Exception :
            jkbLib.error(traceback.format_exc())

        

    def restart(self):
        jkbLib.rmPid('agent')
        os._exit(0)
    
    def initPlug(self,plug):
        if plug['pluginFileName'] == 'SnmpPlugin':#关闭自动更新，因为要修改插件文件被更新覆盖还原就无效了
            return None
        try:
            if os.path.exists('plugin/'+plug['pluginFileName']+'.py'):
                md = jkbLib.getMD5('plugin/'+plug['pluginFileName']+'.py')
                if md!= plug['md5']:
                    os.remove('plugin/'+plug['pluginFileName']+'.py')
                    jkbLib.download(jkbConfig.jkbServer+'/agent/plugin/'+plug['pluginFileName']+'.py',
                                    'plugin/'+plug['pluginFileName']+'.py')
            else :
                jkbLib.download(jkbConfig.jkbServer+'/agent/plugin/'+plug['pluginFileName']+'.py',
                                    'plugin/'+plug['pluginFileName']+'.py')
        except Exception :
            jkbLib.error(traceback.format_exc())
       
    def getUsrPluginSet(self):
        try:
            url = jkbConfig.configUrl + '&mac=' + str(self.mac)+'&ip='+str(self.ip)+'&t='+self.os_type
            res =  urllib2.urlopen(url)
            redata = res.read()
            res.close()
            redata = jkbLib.decode(redata, jkbConfig.jkbDataKey)
            return json.loads(redata)
        except Exception :
            jkbLib.error(traceback.format_exc())



    def postData(self):
        try:
            reData={}
            for taskId in self.objList:
                obj = self.objList[taskId+'']
                reData[taskId+''] = obj.returnData()
                obj.clearData()
            try:
                reData = json.dumps(reData,ensure_ascii=False)
            except Exception:
                try:
                    reData=str(reData)
                    reData=reData.encode('UTF8',errors="ignore")
                    reData=reData.decode('UTF8',errors="ignore")
                    reData=dict(eval(reData))
                    reData = json.dumps(reData,ensure_ascii=False)
                except Exception:
                    jkbLib.error('json.dumps loss!')
                    jkbLib.error(traceback.format_exc())
                    reData={}
                    reData = json.dumps(reData,ensure_ascii=False)
                
            if zlib:
                reData = reData.encode('UTF8') 
                reData = zlib.compress(reData, 9)
                if base64:
                    reData = base64.encodestring(reData)
                else:
                    reData = reData.encode('base64') 
            
            parms = {'data':reData,'post_time':self.post_time}
            parms = parse.urlencode(parms)
            parms=parms.encode('UTF8')
            command=''
            url = jkbConfig.postUrl + '&mac=' + str(self.mac)+'&ip='+str(self.ip)
            try:
                res =  urllib2.urlopen(urllib2.Request(url , parms))
                command = res.read()
                res.close()
            except Exception:
                jkbLib.error(traceback.format_exc())
                res =  urllib2.urlopen(urllib2.Request(url , parms))
                command = res.read()
                res.close()
            command = jkbLib.decode(command, jkbConfig.jkbDataKey)
            command = json.loads(command)
            if command == '':
                jkbLib.error('command is none!!')
                return ''
            return command
        except Exception :
            jkbLib.error(traceback.format_exc())

    def postlog(self):
        try:
            logStr = jkbLib.readLog()
            parms = {'data':logStr}
            parms = parse.urlencode(parms)
            parms=parms.encode('UTF8')  
            urllib2.urlopen(urllib2.Request(jkbConfig.logUrl , parms))
        except Exception :
            jkbLib.error(traceback.format_exc())

class MasterProcessMonitor(threading.Thread):

    def __init__(self, agentProcess):
        self.agentProcess = agentProcess
        self.lock = threading.Lock()
        self.lastHeartbeat = time.time()
        self.running = True
        threading.Thread.__init__(self)

    def run( self ):
        while self.running:
            time.sleep(4)
            try:
                try:
                    self.lock.acquire()

                    if (time.time()-self.lastHeartbeat) > 12:
                        self.agentProcess.stop()
                        jkbLib.rmPid('agent')    
                        os._exit(0)

                finally:
                    self.lock.release()

            except Exception :
                jkbLib.error(traceback.format_exc())
                raise

    def stop( self ):
        self.running = False

    def heartbeat(self):
        try:
            self.lock.acquire()
            self.lastHeartbeat = time.time()
        finally:
            self.lock.release()

class MasterPingReader(threading.Thread):

    def __init__(self, agentProcess, masterMonitor):
        self.agentProcess = agentProcess
        self.masterMonitor = masterMonitor
        threading.Thread.__init__( self )
       

    def run(self):
        while True:
            time.sleep(4)
            try:
                line = sys.stdin.readline()
                if not line:
                    continue

                if line == 'stop\n':
                    try:
                        jkbLib.rmPid('agent')
                        self.agentProcess.stop()
                        self.masterMonitor.stop()
                    finally:
                        os._exit(0)
                
                if line == 'restart\n':
                    self.agentProcess.restart()
                    
                if line == 'ping\n':
                    self.masterMonitor.heartbeat()
                    continue

            except Exception :
                jkbLib.error(traceback.format_exc())


if __name__ == "__main__":
    agentPid = os.getpid()
    try:
        pid = jkbLib.readPid('agent')
    except IOError:
        pid = 0
    
    if  pid>0:
        if jkbLib.UsePlatform() == 'Windows' :
            isRun=jkbLib.checkPidWin(pid)
        else:
            isRun=jkbLib.checkPidLinux(pid)
        if isRun:
            jkbLib.printout('Program has been started, the process PID：' +str(pid))
            sys.exit(1)

    jkbLib.writePid(agentPid,'agent')
    
    jkbLib.info( 'Starting agent process' )
    jkbLib.printout('Starting agent process')
    parentPid = None
    try:
        if len(sys.argv) > 1:
            parentPid = sys.argv[1]
    except Exception :
        jkbLib.error(traceback.format_exc())

    try:
        agentProcess = AgentProcess()
        agentProcess.setName('AgentProcess')
        agentProcess.start()
        
        monitor = MasterProcessMonitor(agentProcess)
        monitor.setName('MasterProcessMonitor')
        monitor.start()

        pingReader = MasterPingReader(agentProcess, monitor)
        pingReader.setName('MasterPingReader')
        pingReader.start()

        jkbLib.info('Started agent process, parent PID:' +str(parentPid)+' the agent PID:'+str(agentPid))
        jkbLib.printout('Started agent process, parent PID:' +str(parentPid)+' the agent PID:'+str(agentPid))

    except Exception :
        jkbLib.error(traceback.format_exc())

