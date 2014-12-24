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
Jiankongbao SQLserver plugin
author@huohuiliang
"""



from lib import jkbLib
import traceback
import pyodbc


from p_class import plugins



class SQLserverPlugin(plugins.plugin):

    def __init__(self,taskId,taskConf,agentType,pluginId):
        plugins.plugin.__init__(self,taskId,taskConf,agentType,pluginId)
        self.driver='SQL Server'


    def setData(self,data):
        try:
            self.lock.acquire()
            self.DataList.append(data)
        finally:
            self.lock.release()
    

    
    def getSQLData(self):
        try:
            redata={}
            host=str(self.taskConf['host'])
            uid=str(self.taskConf['user'])
            pwd=str(self.taskConf['password'])
            port=str(self.taskConf['port'])
            appname=str(self.taskConf['appname'])
            

            try:
                cnxn = pyodbc.connect('DRIVER={'+self.driver+'};SERVER='+host
                                      +';Port='+port+';UID='+uid+';PWD='+pwd
                                      +';database='+appname+';autocommit=True')
            except Exception :
                try:
                    self.driver='SQL Native Client'
                    cnxn = pyodbc.connect('DRIVER={'+self.driver+'};SERVER='+host
                                      +';Port='+port+';UID='+uid+';PWD='+pwd
                                      +';database='+appname+';autocommit=True')
                except Exception:
                    self.driver='SQL Server Native Client 10.0'
                    cnxn = pyodbc.connect('DRIVER={'+self.driver+'};SERVER='+host
                                          +';Port='+port+';UID='+uid+';PWD='+pwd
                                          +';database='+appname+';autocommit=True')
            
            cursor = cnxn.cursor()
            
            #静态状态
            sql='''select 
            cpu_count,
            hyperthread_ratio,
            scheduler_count,
            physical_memory_in_bytes / 1024 / 1024 as physical_memory_mb,
            virtual_memory_in_bytes / 1024 / 1024 as virtual_memory_mb
            from sys.dm_os_sys_info'''
            cursor.execute(sql)
            #row = cursor.fetchall()
            row = cursor.fetchone()
            
            redata['cpu_count']=row[0]
            redata['hyperthread_ratio']=row[1]
            redata['scheduler_count']=row[2]
            redata['physical_memory_mb']=row[3]
            redata['virtual_memory_mb']=row[4]

            
            #连接数
            sql='SELECT COUNT(*) AS CONNECTIONS FROM sys.dm_exec_connections'
            cursor.execute(sql)
            row = cursor.fetchone()
            redata['connections']=row[0]
            
            #空间使用情况
            cursor.execute("sp_spaceused")

            row= cursor.fetchone()
            
            redata['database_name']=row[0]
            redata['database_size']=row[1]
            redata['unallocated_space']=row[2]
            
            cursor.nextset()
            
            row= cursor.fetchone()
            
            redata['reserved']=row[0]
            redata['data']=row[1]
            redata['index_size']=row[2]
            redata['unused']=row[2]
            
            #io_req
            cursor.execute('select count(*) as io_req from sys.dm_io_pending_io_requests')
            row= cursor.fetchone()
            redata['io_req']=row[0]
            
            #other
            cursor.execute('select * from sys.dm_os_performance_counters')
            row= cursor.fetchall()
            for val in row:
                val[1]=str(val[1]).strip(' ')
                val[2]=str(val[2]).strip(' ')
                val[3]=str(val[3]).strip(' ')
                if val[1]=='Lock Waits/sec' and val[2] == '_Total':
                    redata['lock_wait']=val[3]
                    
                if val[1]=='Average Wait Time (ms)' and val[2] == '_Total':
                    redata['lock_wait_time']=val[3]
                    
                if val[1]=='Log File(s) Size (KB)' and val[2] == appname:
                    redata['log_file_size']=val[3]
                    
                if val[1]=='Log File(s) Size (KB)' and val[2] == '_Total':
                    redata['total_log_file_size']=val[3]
                    
                if val[1]=='Log File(s) Used Size (KB)' and val[2] == appname:
                    redata['log_file_used_size']=val[3]
                    
                if val[1]=='Log File(s) Used Size (KB)' and val[2] == '_Total':
                    redata['total_log_file_used_size']=val[3]
                    
                if val[1]=='Errors/sec' and val[2] == 'User Errors':
                    redata['error']=val[3]
                    
                if val[1]=='Target Server Memory (KB)':
                    redata['target_server_memory']=val[3]
                    
                if val[1]=='Total Server Memory (KB)':
                    redata['total_server_memory']=val[3]
                    
                if val[1]=='Batch Requests/sec':
                    redata['req']=val[3]
            cursor.close()
            cnxn.close()
            
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        return redata


    
    def getData(self):
        status_content = {}
        try: 
            status_content=self.getSQLData()
            self.intStatus()
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())

        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':status_content, 'error_info':self.error_info})
