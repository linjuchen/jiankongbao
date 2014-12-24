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
Jiankongbao snmp plugin
author@huohuiliang
"""


import time
from lib import jkbLib
import traceback
import re

from p_class import plugins

import subprocess

from lib import jkbLib

try:
    from  urllib import parse
except ImportError:
    import urllib as parse

class SnmpPlugin(plugins.plugin):

    def __init__(self,taskId,taskConf,agentType,pluginId):
        plugins.plugin.__init__(self,taskId,taskConf,agentType,pluginId)
        self.snmpwalk = 'snmpwalk'
        self.cmd=''

    def setData(self,data):
        try:
            self.lock.acquire()
            self.DataList.append(data)
        finally:
            self.lock.release()

    def execSnmp(self):
        data = ''
        cht = 0
        try:
            while(cht < 1):
                returnstr=subprocess.Popen(self.cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
                data = returnstr.stdout.read()
                error= returnstr.stderr.read()
                if error :
                    try:
                        error=error.decode("utf-8")
                    except Exception:
                        error=error.decode("GBK")
                    jkbLib.error(self.logHead + error)
                    self.code = 'A002'
                    self.error_info = error
                    data = ''
                    cht += 1
                    error = True
                else :
                    break

        except Exception:
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
            data=''
            
        return data

    
    def createCmd(self,oid):
        if self.taskConf['snmp_authtype'] == 'sha' :
            authtype = 'SHA'
        else :
            authtype = 'MD5'
            
        if self.taskConf['snmp_v'] == '3' :
            arr = (self.snmpwalk,' -v 3 -u ',self.taskConf['snmp_user'],' -a ',
                   authtype,' -A "',self.taskConf['snmp_pass'],'" -l authNoPriv ',
                   self.taskConf['snmp_ip'],':'+self.taskConf['snmp_port'],' ',oid)
            self.cmd = ''.join(arr)
        else :
            arr = (self.snmpwalk,' -v 2c -c ', self.taskConf['snmp_community'],' ',
                   self.taskConf['snmp_ip'],':'+self.taskConf['snmp_port'],' ',oid)
            self.cmd = ''.join(arr)
            
    def dataToArr(self,data):
        rem = re.compile(r'::([^\.]+)\.([0-9]+) = ([^\n\r]*)',re.M)
        try :
            pyInfo = jkbLib.getPythonVer() 
            if pyInfo[0] == '3':
                data = data.decode("utf-8")
        except Exception:
            try:
                data = data.decode("GBk")
            except Exception:
                data = data.decode("cp1252").encode('utf-8').decode("utf-8")
        try:
            matches = rem.findall(data)
        except Exception:
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        data = {}

        maxNum = 256
        for val in matches :
            if val[0] in self.soid:
                if val[0] in data:
                    if len(data[val[0]]) >= maxNum:
                        continue
                    try:
                        data[val[0]][val[1]]=parse.quote_plus(val[2])
                    except Exception:
                        jkbLib.error(self.logHead + traceback.format_exc())
                        self.errorInfoDone(traceback.format_exc())
                else :
                    data[val[0]]={}
                    try:
                        data[val[0]][val[1]]=parse.quote_plus(val[2])
                    except Exception:
                        jkbLib.error(self.logHead + traceback.format_exc())
                        self.errorInfoDone(traceback.format_exc())
        return data
    
    def getDataByoids(self):
        data = {}
        for oid in self.soid : 
            self.createCmd(oid)
            tmp = self.execSnmp()
            if tmp =='':
                continue
            tmp = self.dataToArr(tmp)
            for val in tmp :
                data[val] = tmp[val]
        return data

    def checkTpye(self,_type):
        if _type == 'cpu' :
            self.soid = ['ssCpuRawUser','ssCpuRawNice','ssCpuRawSystem',
                    'ssCpuRawIdle','ssCpuRawWait','ssCpuRawKernel',
                    'ssCpuRawInterrupt','ssCpuRawSoftIRQ']
            data = self.getDataByoids()
            return data
            
        elif _type == 'cpu_windows' :
            oid = 'hrProcessorLoad'
            self.soid = ['hrProcessorLoad']
            self.createCmd(oid)
            data = self.execSnmp()
            if data == '' :
                self.code='A002'
            return self.dataToArr(data)
            
        elif _type == 'diskio' :
            self.soid = ['diskIODevice','diskIONRead','diskIONWritten',
                    'diskIOReads','diskIOWrites']
            data = self.getDataByoids()
            return data
            
        elif _type == 'diskstore' :
            oid = 'hrStorageTable'
            self.soid = ['hrStorageType','hrStorageDescr','hrStorageAllocationUnits',
                    'hrStorageSize','hrStorageUsed']
            self.createCmd(oid)
            data = self.execSnmp()
            if data == '' :
                self.code='A002'
            return self.dataToArr(data)
            
        elif _type == 'load' :
            oid = 'laLoadFloat'
            self.soid = ['laLoadFloat']
            self.createCmd(oid)
            data = self.execSnmp()
            if data == '' :
                self.code='A002'
            return self.dataToArr(data)
            
        elif _type == 'mem' :
            oid = 'memory'
            self.soid = ['memTotalSwap','memAvailSwap','memTotalReal',
                    'memAvailReal','memBuffer','memCached']
            self.createCmd(oid)
            data = self.execSnmp()
            if data == '' :
                self.code='A002'
            return self.dataToArr(data)
            
        elif _type == 'mem_windows' :
            oid = 'hrStorageTable'
            self.soid = ['hrStorageType','hrStorageDescr','hrStorageAllocationUnits',
                    'hrStorageSize','hrStorageUsed']
            self.createCmd(oid)
            data = self.execSnmp()
            if data == '' :
                self.code='A002'
            return self.dataToArr(data)
            
        elif _type == 'netio' :
            self.soid = ['ifIndex','ifDescr','ifInOctets',
                    'ifOutOctets','ifHCInOctets','ifHCOutOctets',
                         'ifInUcastPkts','ifOutUcastPkts',
                         'ifMtu','ifSpeed']
            data = self.getDataByoids()
            return data

        elif _type == 'procsum' :
            oid = 'hrSystemProcesses'
            self.soid = ['hrSystemProcesses']
            self.createCmd(oid)
            data = self.execSnmp()
            if data == '' :
                self.code='A002'
            return self.dataToArr(data)
            
        elif _type == 'sys_info' :
            self.soid = ['sysName','hrSystemUptime','sysDescr']
            data = self.getDataByoids()
            return data
            
        else  :
            return {}
            
        

    def getData(self):
        getData = {}
        try:
            _types = self.taskConf['snmp_list']
            for _type in _types :
                getData[_type] = self.checkTpye(_type)
                
            self.intStatus()
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())

        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':getData, 'error_info':self.error_info})

