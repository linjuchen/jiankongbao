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
Jiankongbao mysql plugin
author@huohuiliang
"""


import time
from lib import jkbLib
import traceback


from p_class import plugins



class MySQLPlugin(plugins.plugin):

    def __init__(self,taskId,taskConf,agentType,pluginId):
        plugins.plugin.__init__(self,taskId,taskConf,agentType,pluginId)

    def setData(self,data):
        try:
            self.lock.acquire()
            self.DataList.append(data)
        finally:
            self.lock.release()

        
    def getData(self):
        redata = {}
        try:
            import MySQLdb
            key_variables = ['log_slow_queries', 'slow_launch_time', 'max_connections', 'key_buffer_size', 
            'tmp_table_size', 'max_heap_table_size', 'table_open_cache', 'thread_cache_size', 'query_cache_limit',
            'query_cache_min_res_unit', 'query_cache_size', 'query_cache_type', 'query_cache_wlock_invalidate', 
            'open_files_limit']
            
            key_status = ['Slow_launch_threads', 'Slow_queries', 'Max_used_connections', 'Key_read_requests', 
            'Key_reads', 'Key_blocks_unused', 'Key_blocks_used', 'Created_tmp_disk_tables', 'Created_tmp_files', 
            'Created_tmp_tables', 'Open_tables', 'Opened_tables', 'Threads_cached', 'Threads_connected', 
            'Threads_created', 'Threads_running', 'Qcache_free_blocks', 'Qcache_free_memory', 'Qcache_hits', 
            'Qcache_inserts', 'Qcache_lowmem_prunes', 'Qcache_not_cached', 'Qcache_queries_in_cache', 
            'Qcache_total_blocks', 'Sort_merge_passes', 'Sort_range', 'Sort_rows', 'Sort_scan','Open_files',
            'Table_locks_immediate','Table_locks_waited','Handler_read_first','Handler_read_key',
            'Handler_read_next','Handler_read_prev','Handler_read_rnd','Handler_read_rnd_next','Com_change_db',
            'Com_delete','Com_insert','Com_select','Com_update','Com_update_multi','Connections',
            'Bytes_received','Bytes_sent']
            
            
            keys = ''
            for key in key_variables :
                keys += "'"+key+"',"
            keys = keys.strip(',')

            self.taskConf['port'] = int(self.taskConf['port'])
            conn = MySQLdb.connect(host=self.taskConf['host'],user=self.taskConf['user'],
                                   passwd=self.taskConf['password'],port=self.taskConf['port'])
            cur=conn.cursor()
            sql = "show variables where Variable_name in ("+keys+")";
            cur.execute(sql)
            results=cur.fetchall()
            for key in results :
                redata[key[0]] = key[1]
                
            keys = ''
            for key in key_status :
                keys += "'"+key+"',"
            keys = keys.strip(',')
            sql = "show global status where Variable_name in ("+keys+")";
            cur.execute(sql)
            results=cur.fetchall()
            for key in results :
                redata[key[0]] = key[1]
            cur.close()
            conn.close()

            self.intStatus()
            
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        
        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':redata, 'error_info':self.error_info})
