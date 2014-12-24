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
Jiankongbao iis plugin
author@huohuiliang
"""

from config import jkbConfig
import time
from lib import jkbLib
import traceback
import subprocess
import os
import re
from  xml.dom import  minidom

from p_class import plugins



class IisPlugin(plugins.plugin):

    def __init__(self,taskId,taskConf,agentType,pluginId):
        plugins.plugin.__init__(self,taskId,taskConf,agentType,pluginId)
        self.stat=True
        self.tmpPath='tmp/'
        self.tmpPathWin=jkbLib.getPath() +self.tmpPath
        self.tmpPathWin=self.tmpPathWin.replace('/', '\\')
        self.seekNum=0
        self.lastFile=''
        self.checkConf()
        self.IisVer=6


    def setData(self,data):
        try:
            self.lock.acquire()
            self.DataList.append(data)
        finally:
            self.lock.release()
    
    def getGMT(self):
        gmt=time.gmtime()
        return int(time.mktime(time.strptime(str(gmt.tm_year)
                                            +'-'+str(gmt.tm_mon)
                                            +'-'+str(gmt.tm_mday)
                                            +' '+str(gmt.tm_hour)
                                            +':'+str(gmt.tm_min)
                                            +':'+str(gmt.tm_sec)
                                            , '%Y-%m-%d %H:%M:%S')))
    
    def checkConf(self):
        if not os.path.exists('iistrace.guid'):
            jkbLib.download(jkbConfig.jkbServer+'/agent/plugin/iistrace.guid','plugin/iistrace.guid')
    
    def doCmd(self, cmd) :
        returnstr=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
        data = returnstr.stdout.read()
        return returnstr
    
    def startLog(self):
        cmd = 'del '+self.tmpPathWin+'workload.xml'
        self.doCmd(cmd)
        cmd = 'logman start "IIS Trace" -pf plugin/iistrace.guid -ct perf -o '+self.tmpPath+'iis.etl -ets'
        self.doCmd(cmd)
    
    def closeLog(self):
        cmd = 'logman stop "IIS Trace" -ets'
        self.doCmd(cmd)
        cmd = 'tracerpt '+self.tmpPath+'iis.etl -f XML  -report '+self.tmpPath+'workload.xml'
        self.doCmd(cmd)
        cmd = 'del '+self.tmpPathWin+'iis.etl'
        self.doCmd(cmd)


    def get_attrvalue(self, node, attrname):
        return str(node.getAttribute(attrname))
    
    def get_nodevalue(self, node, index = 0):
        return str(node.childNodes[index].nodeValue)
    
    def get_xmlnode(self, node,name):
        return node.getElementsByTagName(name) 
    
    def formartIISData(self):
        try:
            logPath = self.tmpPath+'workload.xml'
            if  not os.path.exists(logPath):
                return {}
                
            doc = minidom.parse(logPath) 
            root = doc.documentElement
            Tables = self.get_xmlnode(root,'Table')
            redata={}
            
            tabType=''
            nodType=''
            tabNameS=['httpRespTime', 'topUrls', 'siteRequests', 'siteResponseTime', 'siteBytesSent', 'client']
            datNameS=['requestType', 'url', 'siteId', 'computer']
            for tab in Tables: 
                tabName  = self.get_attrvalue(tab,'name')
                if tabName in tabNameS:
                    tabType = tabName
                    nodType =''
                    redata[tabType]={}
                    Items  = self.get_xmlnode(tab,'Item')
                    for item in Items:
                        Datas  = self.get_xmlnode(item,'Data')
                        for Dat in Datas:
                            datName=self.get_attrvalue(Dat,'name') 
                            if datName  in datNameS:
                                if  not (tabName =='topUrls' and  datName =='siteId'):
                                    nodType = self.get_nodevalue(Dat)
                                    redata[tabType][nodType]={}
                            else:
                                redata[tabType][nodType][datName] = self.get_nodevalue(Dat)
            self.intStatus()
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        return redata
        
        
    def formartIIS6Data(self):
        try:
            logPath = self.tmpPath+'workload.xml'
            if  not os.path.exists(logPath):
                return {}
                
            doc = minidom.parse(logPath) 
            root = doc.documentElement
            redata={}
            redata['client']={}
            redata['client']['Client']={}
            try:
                nod = self.get_xmlnode(root,'cpu_speed')
                cpu_speed=self.get_nodevalue(nod[0])
                redata['client']['Client']['clock'] = cpu_speed
            except Exception :
                self.IisVer=7
                return self.formartIISData()
            
            try:
                nod = self.get_xmlnode(root,'memory')
                memory=self.get_nodevalue(nod[0])
                redata['client']['Client']['memory'] = memory
            except Exception :
                redata['client']['Client']['memory'] = '-'
            
            nod = self.get_xmlnode(root,'build')
            build=self.get_nodevalue(nod[0])
            redata['client']['Client']['build'] = build
            
            nod = self.get_xmlnode(root,'processors')
            processors=self.get_nodevalue(nod[0])
            redata['client']['Client']['processors'] = processors
            
            redata['client']['Client']['architecture'] = '-'
            
            Tables = self.get_xmlnode(root,'table')
            for tab in Tables: 
                title  = self.get_attrvalue(tab,'title')
                if title =='Sites with the Most Requests':
                    redata['siteRequests']={}
                    sites=self.get_xmlnode(tab,'site')
                    for site in sites:
                        site_id=self.get_attrvalue(site,'id')
                        
                        rates=self.get_xmlnode(site,'rate')
                        rate=self.get_nodevalue(rates[0])
                        
                        response_times=self.get_xmlnode(site,'response_time')
                        response_time=self.get_nodevalue(response_times[0])
                        
                        if site_id in redata['siteRequests']:
                            redata['siteRequests'][site_id]['requestRate']=rate
                            redata['siteRequests'][site_id]['responseTime']=response_time
                        else:
                            redata['siteRequests'][site_id]={}
                            redata['siteRequests'][site_id]['requestRate']=rate
                            redata['siteRequests'][site_id]['responseTime']=response_time
                            
                elif title =='Sites with the Most Bytes Sent':
                    redata['siteBytesSent']={}
                    sites=self.get_xmlnode(tab,'site')
                    for site in sites:
                        site_id=self.get_attrvalue(site,'id')
                        
                        bytes=self.get_xmlnode(site,'bytes')
                        byte=self.get_nodevalue(bytes[0])
                        
                        if site_id in redata['siteBytesSent']:
                            redata['siteBytesSent'][site_id]['bytesSentRate']=byte
                        else:
                            redata['siteBytesSent'][site_id]={}
                            redata['siteBytesSent'][site_id]['bytesSentRate']=byte
                            
                elif title =='Http Requests Response Time Statistics':
                    redata['httpRespTime']={}
                    requests=self.get_xmlnode(tab,'requests')
                    for request in requests:
                        type=self.get_attrvalue(request,'type')
                        if type=='Static HTTP':
                            cached=self.get_attrvalue(request,'cached')
                            if cached == 'true':
                                type='httpNonCached'
                            else:
                                type='staticCachedHttp'
                        elif type=='ASP':
                            type='asp'
                        elif type=='CGI':
                            type='cgi'
                        
                        response_times=self.get_xmlnode(request,'response_time')
                        response_time=self.get_nodevalue(response_times[0])
                        
                        requestRates=self.get_xmlnode(request,'rate')
                        requestRate=self.get_nodevalue(requestRates[0])
                        redata['httpRespTime'][type]={}
                        redata['httpRespTime'][type]['responseTime']=response_time
                        redata['httpRespTime'][type]['requestRate']=requestRate
                        
                        
                    summarys=self.get_xmlnode(tab,'summary')
                    for summary in summarys: 
                        type=self.get_attrvalue(summary,'type')
                        if type == 'totals':
                            type='httpRespTimeTotal'
                            response_times=self.get_xmlnode(summary,'response_time')
                            response_time=self.get_nodevalue(response_times[0])
                            
                            requestRates=self.get_xmlnode(summary,'rate')
                            requestRate=self.get_nodevalue(requestRates[0])
                            redata['httpRespTime'][type]={}
                            redata['httpRespTime'][type]['responseTime']=response_time
                            redata['httpRespTime'][type]['requestRate']=requestRate
            self.intStatus()
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        return redata

    def getIisLogData(self):
        logPath = self.taskConf['logPath']
        logPath = logPath.replace('\/', "/")
        logPath = logPath.strip('/')
        if self.IisVer==6:
            statusNum=11
            logPath = logPath+'/ex'+jkbLib.date(time.time(), format = '%y%m%d')+'.log'
        else:
            statusNum=10
            logPath = logPath+'/u_ex'+jkbLib.date(time.time(), format = '%y%m%d')+'.log'
        logArr={}
        st_time=self.getGMT() - self.interval
        if  os.path.exists(logPath):
            if self.lastFile=='' and self.seekNum == 0:
                pos=self.getCurPos(st_time, logPath)
                if pos < 0:
                    return logArr
                self.seekNum=pos
            elif self.lastFile != logPath  and self.seekNum != 0:
                self.seekNum=0
                
            pf = open(logPath,'r')
            pf.seek(self.seekNum, 0)
            logStr = pf.read()
            pf.close()
            if not logStr:
                return logArr
            self.seekNum+=len(logStr)
            self.lastFile=logPath
            rem = re.compile(r'([^\n\r]+)',re.M)
            matches = rem.findall(logStr)
            logArr['sum']=0
            for m in  matches:
                if not m:
                    continue
                arr=m.split(' ')
                if len(arr) < statusNum:
                    continue
                code=str(arr[statusNum])
                if len(code)>4 :
                    continue
                if int(code) < 2:
                    continue
                logArr['sum']+=1
                if code in logArr:
                    logArr[code]+=1
                else:
                    logArr[code]=1

        return logArr
        
    def getCurPos(self, st_time, logPath):
        seekPos=0
        while True:
            tmp=0
            pf = open(logPath,'r')
            pf.seek(seekPos, 0)
            logStr = pf.read(50000).strip()
            pf.close()
            tmp_t=st_time
            if not logStr:
                return -1
            while True:
                t=jkbLib.date(tmp_t, format = '%Y-%m-%d %H:%M')
                pos = logStr.find(t)
                if pos > 0 :
                    return seekPos+pos
                tmp+=1
                tmp_t -= 60
                if tmp > 20 :
                    break
            seekPos+=50000


    
    def getData(self):
        status_content = {}
        try:
            if self.stat :
                self.startLog()
                self.stat=False
            else:
                self.closeLog()
                if self.IisVer==6:
                    status_content['logman']=self.formartIIS6Data()
                else:
                    status_content['logman']=self.formartIISData()
                self.startLog()
                
            status_content['iislog']=self.getIisLogData()
            
            self.intStatus()
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())

        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':status_content, 'error_info':self.error_info})
