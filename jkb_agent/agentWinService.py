# -*- coding: utf-8 -*-
#pyWin32/pyWin64 
#agentWinService install 
#agentWinService start   
#agentWinService stop    
#agentWinService debug   
#agentWinService remove  

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
Jiankongbao windows service control
author@huohuiliang
"""


import win32service
import win32serviceutil
import win32event
import time
import subprocess
from lib import jkbLib


class JKBAgentService(win32serviceutil.ServiceFramework):
    _svc_name_ = "JKBAgentService"
    _svc_display_name_ = "JKBAgentService"
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcDoRun(self):
        import servicemanager
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,servicemanager.PYS_SERVICE_STARTED,(self._svc_name_, ''))
        self.timeout=100
        self.obj = None
        while 1:
            rc=win32event.WaitForSingleObject(self.hWaitStop,self.timeout)
            if rc == win32event.WAIT_OBJECT_0:
                break
            else:
                if  self.obj is None  or self.obj.poll() is not None :
                    jkbLib.rmPid('master')
                    jkbLib.rmPid('agent')
                    self.obj = self.startAgentProcess()
                time.sleep(60)
        return

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        subprocess.Popen(['python',jkbLib.getPath()+'jkbMaster.py','stop'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        return
    
    def startAgentProcess(self):
        return  subprocess.Popen(['python',jkbLib.getPath()+'jkbMaster.py','start'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
  

if __name__=='__main__':
    win32serviceutil.HandleCommandLine(JKBAgentService) 
