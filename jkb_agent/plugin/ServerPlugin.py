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
Jiankongbao WinserverPlugin
author@huohuiliang
"""


from lib import jkbLib
import traceback

from p_class import plugins
import os
import psutil


class ServerPlugin(plugins.plugin):

    def __init__(self,taskId,taskConf,agentType,pluginId):
        plugins.plugin.__init__(self,taskId,taskConf,agentType,pluginId)
        self.cpu_total_time=0
        self.cpu_idle_time=0


    def setData(self,data):
        try:
            self.lock.acquire()
            self.DataList.append(data)
        finally:
            self.lock.release()
    
    
    def data_format_KB(self, data):
        data = int(data)
        data = data/1024
        data="%.2f" % data
        data = float(data)
        return data

    def data_format_MB(self, data):
        data = int(data)
        data = data/1024/1024
        data="%.2f" % data
        data = float(data)
        return data
    
    def data_format_GB(self, data):
        data = int(data)
        data = data/1024/1024/1024
        data="%.2f" % data
        data = float(data)
        return data

    def data_format_Ratio(self, hit, total):
        hit = int(hit)
        total = int(total)
        if total == 0 :
            return 0
        data = (hit*100)/total
        data = "%.2f" % data
        data = float(data)
        return data

    def get_win_mem_info(self):
        retrunData={}
        try:
            mem=psutil.phymem_usage()
            retrunData['phymem_used']=self.data_format_GB(mem.used)
            retrunData['phymem_free']=self.data_format_GB(mem.free)
            retrunData['phymem_percent']=mem.percent

            virmem=psutil.virtmem_usage()
            retrunData['virmem_used']=self.data_format_GB(virmem.used)
            retrunData['virmem_free']=self.data_format_GB(virmem.free)
            retrunData['virmem_percent']=virmem.percent
        except Exception:
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        
        return retrunData
#缺虚拟内存 
    def get_linux_mem_info(self):
        retrunData={}
        try:
            f = open('/proc/meminfo', 'r')
            for line in f:
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1])
                elif line.startswith('MemFree:'):
                    mem_free = int(line.split()[1])
                elif line.startswith('Buffers:'):
                    mem_buffer = int(line.split()[1])
                elif line.startswith('Cached:'):
                    mem_cache = int(line.split()[1])
                else:
                    continue
            f.close()
            retrunData['phymem_used']=mem_total-mem_free-mem_buffer-mem_cache
            retrunData['phymem_free']=mem_free
            retrunData['phymem_percent']=self.data_format_Ratio(retrunData['phymem_used'], mem_total)
            
        except Exception:
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        return retrunData
        
    
    
    def get_win_CPU_info(self):
        retrunData={}
        try:
            cpu=psutil.cpu_percent()
            retrunData['cpu_percent']=cpu
        except Exception:
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        return retrunData
        
    def get_linux_CPU_info(self):
        retrunData={}
        try:
            f = open('/proc/stat', 'r')
            values = f.readline().split()
            total_time = 0
            for i in values[1:]:
                total_time += int(i)
            idle_time = int(values[4])
            f.close()
            if self.cpu_total_time!=0 and self.cpu_idle_time!=0:
                ntt=total_time-self.cpu_total_time
                nit=idle_time-self.cpu_idle_time
                retrunData['cpu_percent']=float(100) * (ntt - nit)/ntt
                self.cpu_total_time=total_time
                self.cpu_idle_time=idle_time
            else:
                self.cpu_total_time=total_time
                self.cpu_idle_time=idle_time
                retrunData['cpu_percent']=0
        except Exception:
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        return retrunData   
    
    
    def get_win_disk_io_info(self):
        retrunData={}
        try:
            info=psutil.disk_io_counters()
            retrunData['io_read_count']=info.read_count
            retrunData['io_write_count']=info.write_count
            retrunData['io_read_kb']=self.data_format_KB(info.read_bytes)
            retrunData['io_write_kb']=self.data_format_KB(info.write_bytes)
        except Exception:
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        return retrunData

    def get_win_disk_rate_info(self):
        retrunData={}
        try:
            disk=psutil.disk_partitions()
            for val in disk:
                try:
                    one=psutil.disk_usage(val.device)
                    retrunData[val.device]=one.percent
                except Exception:
                    pass
        except Exception:
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        return retrunData
    
#缺IO
    def get_linux_disk_info(self):
        retrunData={}
        try:
            pd = []
            pd_list=[]
            f = open("/proc/filesystems", "r")
            for line in f:
                if not line.startswith("nodev"):
                    pd.append(line.strip())
            f.close()
            f = open('/etc/mtab', "r")
            for line in f:
                if line.startswith('none'):
                    continue
                tmp = line.strip().split()
                ft = tmp[2]
                if ft not in pd:
                    continue
                pd_list.append(tmp[1])
            f.close()
            for i in pd_list:
                dt = os.statvfs(i)
                use = (dt.f_blocks - dt.f_bfree) * dt.f_frsize
                all = dt.f_blocks * dt.f_frsize
                retrunData[i] = self.data_format_Ratio(use, all)
            
        except Exception:
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        return retrunData
    

    def get_win_net_info(self):
        retrunData={}
        try:
            net=psutil.network_io_counters()
            retrunData['net_sent_kb']=self.data_format_KB(net.bytes_sent)
            retrunData['net_recv_kb']=self.data_format_KB(net.bytes_recv)
            retrunData['net_packets_sent']=net.packets_sent
            retrunData['net_packets_recv']=net.packets_recv
        except Exception:
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        return retrunData
    
    def get_linux_net_info(self):
        retrunData={}
        try:
            bytes_recv = 0
            bytes_sent = 0
            pack_recv=0
            pack_sent=0
            f = open("/proc/net/dev", "r")
            all_lines = f.readlines()
            f.close()
            for line in all_lines[2:]:
                fields = line.split(':')
                name = fields[0].strip()
                if name  and fields[1] :
                    tmp = fields[1].split()
                    bytes_recv += int(tmp[0])
                    pack_recv += int(tmp[1])
                    bytes_sent += int(tmp[8])
                    pack_sent += int(tmp[9])
            retrunData['net_sent_kb']=self.data_format_KB(bytes_sent)
            retrunData['net_recv_kb']=self.data_format_KB(bytes_recv)
            retrunData['net_packets_sent']=pack_sent
            retrunData['net_packets_recv']=pack_recv
        except Exception:
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        return retrunData

    def get_win_process_info(self):
        retrunData={}
        try:
            p=psutil.get_process_list()
            retrunData['process']=len(p)
        except Exception:
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        return retrunData

    def get_linux_process_info(self):
        retrunData={}
        try:
            pids = [int(x) for x in os.listdir('/proc') if x.isdigit()]
            retrunData['process']=len(pids)
        except Exception:
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
        return retrunData

    def getData(self):

        status_content = {}
        try:
            if jkbLib.UsePlatform() == 'Windows':
                if 'cpu' in self.taskConf['snmp_list']:
                    status_content['cpu']=self.get_win_CPU_info()
                if 'mem' in self.taskConf['snmp_list']:
                    status_content['mem']=self.get_win_mem_info()
                if 'diskio' in self.taskConf['snmp_list']:
                    status_content['diskio']=self.get_win_disk_io_info()
                if 'diskstore' in self.taskConf['snmp_list']:
                    status_content['diskstore']=self.get_win_disk_rate_info()
                if 'netio' in self.taskConf['snmp_list']:
                    status_content['netio']=self.get_win_net_info()
                if 'procsum' in self.taskConf['snmp_list']: 
                    status_content['procsum']=self.get_win_process_info()
            else:
                if 'cpu' in self.taskConf['snmp_list']:
                    status_content['cpu']=self.get_linux_CPU_info()
                if 'mem' in self.taskConf['snmp_list']:
                    status_content['mem']=self.get_linux_mem_info()
                if 'diskstore' in self.taskConf['snmp_list']:
                    status_content['diskstore']=self.get_linux_disk_info()
                if 'netio' in self.taskConf['snmp_list']:
                    status_content['netio']=self.get_linux_net_info()
                if 'procsum' in self.taskConf['snmp_list']: 
                    status_content['procsum']=self.get_linux_process_info()
                    
            self.intStatus()
        except Exception :
            jkbLib.error(self.logHead + traceback.format_exc())
            self.errorInfoDone(traceback.format_exc())
            
        self.setData({'agentType':self.agentType,'taskId':self.taskId,
        'pluginId':self.pluginId,'code':self.code,'time':self.getCurTime(),
        'data':status_content, 'error_info':self.error_info})
