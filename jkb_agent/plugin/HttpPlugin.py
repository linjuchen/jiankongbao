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
Jiankongbao http plugin
author@huohuiliang
"""


import time
from lib import jkbLib
import traceback
import re
from p_class import plugins
import socket
import math
import random

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
try:
    from  urllib import parse
except ImportError:
    import urllib as parse

class HttpPlugin(plugins.plugin):

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

    
    def getUnRedirectUrl(self, url,username, password, submit_method, parm,cookies,header, host,   timeout=15):
        req =None
        socket.setdefaulttimeout(timeout)
        if submit_method == 1:
            #post
            parms={}
            if parm:
                rem = re.compile(r'([^&]*)=([^&]*)',re.M)
                matches = rem.findall(parm)
                if matches:
                    for val in matches:
                        parms[val[0]]=val[1]
            parms = parse.urlencode(parms)
            parms=parms.encode('UTF8') 
            req = urllib2.Request(url, parms)
        else:
            req = urllib2.Request(url)
    
        req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; JianKongBao Monitor 1.1)')
        if host:
            req.add_header('Host', host)

        if header:
            rem = re.compile(r'([^:\n ]*):([^\n\r]*)',re.M)
            matches = rem.findall(header)
            for val in matches:
                req.add_header(val[0], val[1])
        if username:
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None,url,username,password)
            handler = urllib2.HTTPBasicAuthHandler(password_mgr)
            opener = urllib2.build_opener(RedirctHandler, handler)
        else:
            opener = urllib2.build_opener(RedirctHandler)
            
        if  cookies:
            opener.addheaders.append(('Cookie', cookies))
    
        
        urllib2.install_opener(opener)
        html = None
        response = None
        re_header = None
        re_code =400
        error_info = ''
        resp_time = 0
        try:
            resolve_start_time = self.microtime()
            response = urllib2.urlopen(req)
            resolve_end_time= self.microtime()
            resp_time ='%.3f' % ((resolve_end_time-resolve_start_time)*1000)
            
            if submit_method == 2:
                #head
                html = ''
            else:
                html = response.read()
            if hasattr(response, 'header'):
                re_header = response.header
            else:
                resp=response.info() 
                if hasattr(resp, 'headers'):
                    re_header = resp.headers
                else:
                    re_header = resp.items()
            if hasattr(response, 'status'):
                re_code = response.status
            elif hasattr(response, 'getcode'):
                re_code = response.getcode()
            elif hasattr(response, 'code'):
                re_code = response.code
        except urllib2.URLError:
            if hasattr(urllib2.URLError, 'code'):
                error_info = urllib2.URLError.code
            elif hasattr(urllib2.URLError, 'reason'):
                error_info = urllib2.URLError.reason
            else:
                error_info = 'url reqest error'
        if response:
            response.close()

        return {'code':re_code, 'header':re_header, 'html':html, 'error_info':error_info, 'resp_time':resp_time}

    
    def getHttpData(self):
        resp = {}
        try:
            url=self.taskConf['statusUrl']
            url=url.replace('\/', "/")
            username = self.taskConf['user']
            password = self.taskConf['password']
            parm = self.taskConf['param']
            ip = self.taskConf['ip']
            header = self.taskConf['header']
            cookies = self.taskConf['cookies']
            pattern_type = int(self.taskConf['pattern_type'])
            pattern_str = self.taskConf['pattern_str']
            submit_method = int(self.taskConf['method'])
        
            al_type=['http', 'https']
            rem = re.compile(r'([http|https]+)://([^/:]*)',re.M)
            matches = rem.findall(url)
            host=''
            url_scheme=''
            if matches :
                url_scheme = matches[0][0]
                if  url_scheme in  al_type:
                    host=matches[0][1]
                else:
                    jkbLib.error("can't match the url")
                    self.errorInfoDone("can't match the url")
                    return False
            else:
                jkbLib.error("can't match the url")
                self.errorInfoDone("can't match the url")
                return False
                
            if host == '':
                jkbLib.error("can't match the url")
                self.errorInfoDone("can't match the url")
                return False
            
            dns_resolve_start_time = self.microtime()
            hostInfo=''
            try:
                hostInfo = socket.gethostbyname_ex(host)
            except Exception :
                if not ip:
                    return False
            dns_resolve_end_time = self.microtime()
            dns_resolve_time = (dns_resolve_end_time - dns_resolve_start_time)*1000
            dns_resolve_time = '%.3f' % dns_resolve_time
            url_ip = ''
            if ip:
                url_ip = ip
            else :
                lens = len(hostInfo[2])
                IP_key = random.randint(0, lens)
                IP_key = IP_key - 1
                url_ip = hostInfo[2][IP_key]
            
            if url_ip != host:
                url=url.replace(host, url_ip)

            resp_result= '1'
            resp_err = '0'
            resp_status = ''
            extend = {}
            data = self.getUnRedirectUrl(url,username, password, submit_method, parm, cookies, header, host)
            
            if data['error_info'] :
                resp_result = '0'
                resp_status = data['error_info']
            else:
                resp_status=data['code']
            
            if int(data['code'])>=400:
                resp_result = '0'
        
            if data['error_info'] =='' and submit_method!=2:
                utf_body = data['html']
                utf_body = str(utf_body)
                if pattern_str:
                    rem = re.compile(r'charset=([^"]*)"',re.M)
                    matches = rem.findall(utf_body)
                    if matches:
                        out_char=matches[0]
                        out_char=out_char.lower()
                        if out_char in ['gb2312', 'gbk', 'utf-8']:
                            pattern_str=pattern_str.encode(out_char)
                    if  pattern_type==0:
                        if  pattern_str not in  data['html']:
                            resp_result='0'
                            resp_status = 'HTTP_ERR_NOT_PATTERN'
                    else:
                        if pattern_str  in  data['html']:
                           resp_result='0'
                           resp_status = 'HTTP_ERR_PATTERN'
                           
            resp_header={}
            if data['header']:
                for h in data['header']:
                        if len(h)!=2:
                            rem = re.compile(r'([^:]*):(.*)',re.M)
                            matches = rem.findall(h)
                            if matches:
                                str_h=matches[0][1].strip('\r\n')
                                str_h=str_h.replace('"', '')
                                str_h=str_h.replace("'", "")
                                resp_header[matches[0][0]]=str_h
                        else:
                            str_h=h[1]
                            str_h=str_h.replace('"', '')
                            str_h=str_h.replace("'", "")
                            resp_header[h[0]]=str_h
            
            try:
                resp_status_int=int(resp_status)
                if resp_status_int == 200 :
                    resp_status_int =str(resp_status)+' OK'
                else:
                    resp_status_int =str(resp_status)+' FOUND'
            except:
                resp_status_int='404 FOUND'
            
            if resp_status_int == '' :
                resp_status_int='404 FOUND'

            
            extend['req_method']='GET'
            extend['req_httpv']='1.1'
            extend['resp_httpv'] ='1.1'
            extend['total_time']=data['resp_time']
            extend['namelookup_time']=dns_resolve_time
            extend['connect_time']=dns_resolve_time
            extend['pretransfer_time']=dns_resolve_time
            extend['starttransfer_time']=dns_resolve_time
            extend['speed_download']=0
            extend['size_download']=0
            extend['ip']=url_ip
            
            extend['resp_headers']=resp_header

            resp={'resp_result':resp_result, 'resp_status':resp_status_int, 'resp_time':data['resp_time'], 'resp_err':resp_err, 'extend':extend}
            
            self.intStatus()
            return resp

        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
            return False

    def getData(self):
        status_content = {}
        status_content=self.getHttpData()
        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':status_content, 'error_info':self.error_info})

class RedirctHandler(urllib2.HTTPRedirectHandler):
    """docstring for RedirctHandler"""
    def http_error_301(self, req, fp, code, msg, headers):
        result=None
        resp_h=[]
        try:
            header_str = str(headers)
            rem = re.compile(r'([^\r\n]*)',re.M)
            matches = rem.findall(header_str)
            if matches:
                for h in matches:
                    if h:
                        resp_h.append(h)
            result = urllib2.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)
            result.header = resp_h
            result.status = code
        except Exception :
            try:
                location = headers.get('Location')
                if location and location[0]=="/":
                    url=req.get_full_url()
                    rem = re.compile(r'([http|https]+)://([^/]*)',re.M)
                    matches = rem.findall(url)
                    if matches:
                        re_url=matches[0][0]+'://'+ matches[0][1]
                        re_url=re_url+location
                        headers.replace_header('Location', re_url)
                        result = urllib2.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)
                        result.header = resp_h
                        result.status = code
                    else:
                        jkbLib.error(traceback.format_exc())
                else:
                    jkbLib.error(traceback.format_exc())
            except Exception :
                jkbLib.error(traceback.format_exc())
        return result 
    http_error_302 = http_error_303 = http_error_307 = http_error_301
