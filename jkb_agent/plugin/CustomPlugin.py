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
Jiankongbao custom plugin
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


class CustomPlugin(plugins.plugin):

    def __init__(self,taskId,taskConf,agentType,pluginId):
        plugins.plugin.__init__(self,taskId,taskConf,agentType,pluginId)
        self.obj = None


    def setData(self,data):
        try:
            self.lock.acquire()
            self.DataList.append(data)
        finally:
            self.lock.release()


    def getData(self):
        redata={}
        try:
            if 'filepath' in self.taskConf and self.taskConf['filepath'] != '':
                if not self.obj:
                    filePath=self.taskConf['filepath']
                    filePath=filePath.strip('.py')
                    module_meta = __import__('plugin', globals(), locals(), [str(filePath)]) 
                    class_meta = getattr(module_meta, filePath)
                    c = getattr(class_meta, 'CustomClass')
                    self.obj = c(self)
                redata=self.obj.run()
            else:
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
                rem = re.compile('<pre>([\r|\n|\r\n]*)(.*)</pre>',re.S)
                matches = rem.findall(data)
                if matches :
                    strdata = matches[0][1]
                else :
                    jkbLib.error(self.logHead + ' data format:pre')
                    return False
                rem = re.compile('([^:^\r^\n]*):([^:^\r^\n]*)([\r|\n|\r\n]*)',re.S)
                matches = rem.findall(strdata)
                if not matches :
                    jkbLib.error(self.logHead + ' data format:n')
                    return False
                for  key in  matches :
                    redata[key[0]] = key[1]
            self.intStatus()
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':redata, 'error_info':self.error_info})


