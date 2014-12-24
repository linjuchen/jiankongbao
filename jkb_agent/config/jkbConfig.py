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
Jiankongbao Global configurations.
author@huohuiliang
"""


jkbKey = ''###修改成自己的key

jkbDataKey = 'e03a9d9d4660266f81415dcca2fcce60'

jkbServer = "http://plugin.jiankongbao.com"

versionUrl = jkbServer + "/agent_checkVer.php?key="+jkbKey

configUrl = jkbServer + "/agent_setting.php?key="+jkbKey

logUrl = jkbServer + "/agent_logs.php?key="+jkbKey

postUrl=jkbServer + "/agent_post.php?key="+jkbKey

pythonVer=['2.4','2.6','2.7', '3.2','3.3']

autoUpdate = True

useProxy = False

proxy_host=''

proxy_port=''

upList={jkbServer+'/agent/jkbAgent.py':'jkbAgent.py',
                jkbServer+'/agent/lib/jkbLib.py':'lib/jkbLib.py',
                jkbServer+'/agent/p_class/plugins.py':'p_class/plugins.py',
                jkbServer+'/agent/lib/jkbLogger.py':'lib/jkbLogger.py'}


