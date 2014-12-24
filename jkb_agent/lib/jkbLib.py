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
Jiankongbao lib
author@huohuiliang
"""


import os
from os.path import basename

import time
import datetime

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
import logging
import platform
from hashlib import md5
import ctypes 
import sys
import base64
import subprocess
import socket

def date(unixtime, format = '%m/%d/%Y %H:%M'):
    d = datetime.datetime.fromtimestamp(unixtime)
    return d.strftime(format)

def strtotime(timeStr, format = '%Y-%m-%d %H:%M:%S'):
    time_tuple = time.strptime(timeStr, format)
    timestamp = time.mktime(time_tuple)
    return int(timestamp)
    
def info(str):
    logger = logging.getLogger('JKB')
    FileHandler = logging.FileHandler(getPath()+'log/'+date(time.time(), format = '%Y-%m-%d')+'.log')
    FileHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(FileHandler)
    logger.setLevel(logging.INFO)
    logger.info(str)
    logger.removeHandler(FileHandler)
    FileHandler.close()
    
def error(str):
    logger = logging.getLogger('JKB')
    FileHandler = logging.FileHandler(getPath()+'log/'+date(time.time(), format = '%Y-%m-%d')+'.log')
    FileHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(FileHandler)
    logger.setLevel(logging.INFO)
    logger.error(str)
    logger.removeHandler(FileHandler)
    FileHandler.close()

def url2name(url):
    return basename(urlsplit(url)[2])

def checkPidWin(pid=0):
    cmd='tasklist /FI "PID eq '+str(pid)+'"  /FI "IMAGENAME eq python.exe "'
    returnstr=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
    data = returnstr.stdout.read()
    if len(data) > 150:
        return True
    else :
        return False

def checkPidLinux(pid=0):
    cmd='ps ax |grep '+str(pid)+' |grep python'
    returnstr=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
    data = returnstr.stdout.read()
    if len(data) > 20:
        return True
    else :
        return False

def download(url, localFileName = None):
    homePath = ''
    if UsePlatform() == 'Windows' :
        homePath = getPath()
    localName = url2name(url)
    req = urllib2.Request(url)
    r = urllib2.urlopen(req)
    if localFileName:
        # we can force to save the file as specified name
        localName = homePath + localFileName
    f = open(localName, 'w')
    f.write(r.read())
    f.close()

def getMD5(strFile):
    try:
        fh = open(strFile, "rb")
        m = md5()
        strRead = ""

        while True:
            strRead = fh.read(8096)
            if not strRead:
                break
            m.update(strRead)
        bet = True
        strMd5 = m.hexdigest()
        if fh:
            fh.close()
    except:
        bet = False
        if fh:
            fh.close()
    if bet :
        return strMd5
    else:
        return bet
    
def readPid(pidType):
    pidPath=None
    homePath = ''
    if UsePlatform() == 'Windows' :
        homePath = getPath()
        
    if pidType=='agent':
        pidPath=homePath+'tmp/agentpid.pid'
    else :
        pidPath=homePath+'tmp/masterpid.pid'
    if os.path.exists(pidPath):
        pf = open(pidPath,'r')
        pid = int(pf.read().strip())
        if pid ==0 :
            pid =False
        pf.close()
        return pid
    else :
        return 0
        
    
def readLog():
    logPath=None
    homePath = ''
    if UsePlatform() == 'Windows' :
        homePath = getPath()
    logPath=homePath+'log/'+date(time.time(), format = '%Y-%m-%d')+'.log'
    if os.path.exists(logPath):
        pf = open(logPath,'r')
        logStr = pf.read().strip()
        return logStr
    else:
        return False
    
def writePid(pid,pidType):
    pidPath=None
    homePath = ''
    if UsePlatform() == 'Windows' :
        homePath = getPath()
    if pidType=='agent':
        pidPath=homePath+'tmp/agentpid.pid'
    else :
        pidPath=homePath+'tmp/masterpid.pid'
    pid = str(pid)
    pf = open(pidPath,'w')
    pf.write("%s\n" % pid)
    pf.close()

def rmPid(pidType):
    pidPath=None
    homePath = ''
    if UsePlatform() == 'Windows' :
        homePath = getPath()
    if pidType=='agent':
        pidPath=homePath+'tmp/agentpid.pid'
    else :
        pidPath=homePath+'tmp/masterpid.pid'
    pf = open(pidPath,'w')
    pf.write("0")
    pf.close()
    
def UsePlatform():
    sysstr = platform.system()
    if(sysstr =="Windows"):
        return 'Windows'
    elif(sysstr == "Linux"):
        return 'Linux'
    else:
        return 'Other'
        
def kill(pid):
    """kill function for Win32"""
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(1, 0, pid)
    return (0 != kernel32.TerminateProcess(handle, 0))

def getPath():
    str=os.path.split(os.path.realpath(__file__))
    str=os.path.split(str[0])
    return str[0]+'/'

def printout(data):
    sys.stderr.write(data+'\n')
    
def getPythonVer():
    var = platform.python_version()
    return var[0]+var[1]+var[2]


def decode(strdata, key):
    try:
        m = md5()
        key=key.encode('UTF8')  
        m.update(key)
        key = m.hexdigest()
        l = len(key)
        strdata=strdata.decode('UTF8')
        i = l-1
        while(i>=0):
            kk=str(ord(key[i]))
            le=len(kk)
            kk = kk[le-1:le]
            #tt = kk +'=' + key[i]
            strdata = str_remove(strdata, kk)
            if strdata == '' :
                return ''
            i-=1
        strdata = strdata.encode('UTF8')  
        strdata = base64.b64decode(strdata)
        strdata = strdata.decode('UTF8')
        return strdata
    except Exception :
        return ''
    
def str_remove(strdata, i):
    try:
        i = int(i)
        strdata = str(strdata)
        l = len(strdata)
        tmp_str = strdata
        j=0
        le = len(tmp_str)
        while(j < l):
            if j >= i  :
                if j+1 < le:
                    strdata=strdata[:j] + tmp_str[j+1] + strdata[j+1:]
                else:
                    strdata=strdata[:j] 
            j+=1
        return strdata
    except Exception :
        return ''

def get_mac_address():
    import uuid
    node = uuid.getnode()
    mac = uuid.UUID(int = node).hex[-12:]
    return mac

def get_ip():
    if UsePlatform() == 'Windows' :
        myaddr = socket.gethostbyname(socket.gethostname())
        return myaddr
    else:
        cmd="ifconfig | grep 'inet addr:' | awk '{print $2}'|awk -F ':' '{print $2}'|grep -v '127.0.0.1'"
        returnstr=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
        myaddr = returnstr.stdout.read()
        if not myaddr:
            myaddr='127.0.0.1'
        else:
            myaddr = myaddr.decode('utf8')
            myaddr = myaddr.split("\n")
            myaddr = myaddr[0]
            myaddr = myaddr.strip("\n\r")
        #容错
        if len(myaddr) > 45 :
            myaddr='127.0.0.1'
        return myaddr
