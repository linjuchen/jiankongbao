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
Jiankongbao Master Process
author@huohuiliang
"""


from config import jkbConfig
from lib import jkbLib


import os
import sys
import time


import traceback
import threading
import subprocess

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
    
import signal 

try:
    import json
except ImportError:
    import simplejson as json

masterPid = os.getpid()

class MasterProcess(object):

    def __init__(self):
        self.lock = threading.Lock()
        self.agent = None


    def _send(self, msg):
        try:
            self.lock.acquire()

            if self.agent is None or self.agent.poll() is not None:
                return

            self.agent.stdin.write(msg)
            self.agent.stdin.flush()

            if msg == 'stop\n':
                time.sleep(1)
                self.agent = None

        finally:
            self.lock.release()

    def ping(self):
        return self._send('ping\n'.encode('UTF8'))

    def stop(self):
        return self._send('stop\n'.encode('UTF8'))
    
    def restart(self):
        return self._send('restart\n'.encode('UTF8'))
    


class AgentProcessMonitor(threading.Thread):

    def __init__(self, masterProcess):
        self.masterProcess = masterProcess
        if jkbLib.UsePlatform() == 'Windows' :
            self.agentPath =jkbLib.getPath()+'jkbAgent.py'
            self.cmd = 'python'
        else :
            self.agentPath = os.path.join(sys.path[0],'jkbAgent.py')
            self.cmd = sys.executable
        threading.Thread.__init__(self)
        
    def __del__(self):
        jkbLib.rmPid('agent')
        jkbLib.rmPid('master')

    def _startAgentProcess(self):
        return subprocess.Popen([self.cmd,self.agentPath,
                                 str(masterPid)],stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE)

    def run(self):
        while True:
            try:
                time.sleep(8)
                self.masterProcess.lock.acquire()
                try:
                    if  self.masterProcess.agent is None  or self.masterProcess.agent.poll() is not None :
                        self.masterProcess.agent = self._startAgentProcess()
                except Exception :
                    jkbLib.error(traceback.format_exc())
            finally:
                self.masterProcess.lock.release()


class AgentUpdater(threading.Thread):

    def __init__(self, config, agentDir, masterProcess):
        self.config = config
        self.agentDir = agentDir
        self.checkTime = 1800
        self.masterProcess = masterProcess
        self.homePath = ''
        if jkbLib.UsePlatform() == 'Windows' :
            self.homePath = jkbLib.getPath()
        pf = open(self.homePath+'agentVersion.txt','r')
        self.agentVersion = pf.read().strip()
        pf.close()
        
        threading.Thread.__init__(self)

    def run( self ):
        while True:
            try:
                time.sleep(self.checkTime)
                res = None
                resJson = None
                res = urllib2.urlopen(jkbConfig.versionUrl)
                try :
                    resJson = res.read()
                    resJson = resJson.decode('UTF8')
                    resJson = json.loads(resJson)
                finally:
                    if res is not None:
                        res.close()

                if 'status' not in resJson or resJson['status'] != 'ok':
                    continue

                if 'agentVersion' not in resJson:
                    continue

                agentVersion = resJson['agentVersion']
                if agentVersion != self.agentVersion:
                    self._upgradeAgent(agentVersion)

            except Exception :
                jkbLib.error(traceback.format_exc())

    def _upgradeAgent(self, newAgentVersion):
        try:
            self._downFile(self.config.upList)
            self.masterProcess.restart()
            jkbLib.info('new agent version: ' + newAgentVersion)
            open(self.homePath+'agentVersion.txt','w+').write("%s\n" % newAgentVersion)
            self.agentVersion = newAgentVersion
        except Exception :
            jkbLib.error(traceback.format_exc())

    def _downFile(self,lists):
        try:
            for one in lists:
                jkbLib.download(one,lists[one])
                jkbLib.info('update file :'+lists[one])
        except Exception :
            jkbLib.error(traceback.format_exc())


class Control : 
    def start(self):
        try:
            pid = jkbLib.readPid('master')
        except IOError:
            pid = 0
    
        if  pid>0:
            if jkbLib.UsePlatform() == 'Windows' :
                isRun=jkbLib.checkPidWin(pid)
            else:
                isRun=jkbLib.checkPidLinux(pid)
            if isRun:
                jkbLib.printout('Program has been started, the process ID：'+str(pid))
                sys.exit(1)
        
        try:

            verInfo=jkbLib.getPythonVer()
            if verInfo not in jkbConfig.pythonVer:
                verStr='/'.join(jkbConfig.pythonVer)
                jkbLib.info('当前pyhon版本还没兼容，程序执行中止，目前支持python版本：'+verStr) 
                sys.exit(1)
            pid = str(masterPid)
            jkbLib.writePid(pid,'master')
            print('Starting master process')
            jkbLib.info('Starting master process') 
            masterProcess = MasterProcess()
            monitor = AgentProcessMonitor(masterProcess)
            monitor.setName('AgentProcessMonitor')
            monitor.setDaemon(True)
            monitor.start()
            if jkbConfig.autoUpdate:
                updater = AgentUpdater(jkbConfig, sys.path[0], masterProcess)
                updater.setName('AgentUpdater')
                updater.setDaemon(True)
                updater.start()
            
            print('Started master process')
            jkbLib.info('Started master process')

            while True:
                try:
                    time.sleep(5)
                    masterProcess.ping()
                except Exception :
                    jkbLib.error(traceback.format_exc())

        except KeyboardInterrupt:
            masterProcess.stop()
        except Exception :
            jkbLib.error(traceback.format_exc())

    def stop(self):
        try:
            pid = jkbLib.readPid('master')
        except IOError:
            pid = None
    
        if not pid:
            message = "The process does not exist, the operation aborts"
            jkbLib.printout(message)
            jkbLib.info(message)
            return # not an error in a restart
        # Try killing the daemon process    
        try:
            systype = jkbLib.UsePlatform()
            while 1:
                if systype == 'Linux' :
                    os.kill(pid, signal.SIGTERM)
                else :
                    if jkbLib.kill(pid) :
                        jkbLib.rmPid('agent')
                        jkbLib.rmPid('master')
                        jkbLib.printout('Successful process closes')
                        jkbLib.info('Successful process closes')
                        sys.exit(1)
                    else :
                        jkbLib.printout('Failed to process closes')
                        jkbLib.info('Failed to process closes')
                        jkbLib.rmPid('agent')
                        jkbLib.rmPid('master')
                        sys.exit(1)
                time.sleep(0.1)
        except OSError :
                jkbLib.rmPid('agent')
                jkbLib.rmPid('master')
        jkbLib.printout('Successful process closes')
        jkbLib.info('Successful process closes')

    def restart(self):
        self.stop()
        self.start()
        
    def check(self):
        try:
            pid = jkbLib.readPid('master')
        except IOError:
            pid = None
    
        if not pid:
            message = "Process has closed\n"
            sys.stderr.write(message)
        else:
            message = "The process has been run, the process id:%d\n"
            sys.stderr.write(message % pid)
            
    def helpInfo(self):
        jkbLib.printout("usage: %s install|start|stop|restart|check|help" % sys.argv[0])
        

if __name__ == "__main__":
    Contr=Control()
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            Contr.start()
        elif 'stop' == sys.argv[1]:
            Contr.stop()
        elif 'restart' == sys.argv[1]:
            Contr.restart()
        elif 'check' == sys.argv[1]:
            Contr.check()
        elif 'help' == sys.argv[1]:
            Contr.helpInfo() 
        else:
            jkbLib.printout("未知命令")
            sys.exit(2)
    else:
        jkbLib.printout("usage: %s start|stop|restart|check|help" % sys.argv[0])
        sys.exit(2)
