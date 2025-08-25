#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU监控服务
实时监控GPU状态、内存使用和性能指标
"""

import time
import json
import logging
import threading
import ctranslate2
import psutil
from datetime import datetime
from utils.config_manager import config_manager
from models.translateModel import TranslatorSingleton

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gpu_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class GPUMonitor:
    """GPU监控器"""
    
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.monitor_interval = config_manager.getint('GPU', 'GPU_MONITOR_INTERVAL', 30)
        self.memory_threshold = config_manager.getint('GPU', 'GPU_MEMORY_THRESHOLD', 80)
        self.enable_cleanup = config_manager.getboolean('GPU', 'GPU_MEMORY_CLEANUP', True)
        self.performance_data = []
        self.max_data_points = 1000
        
    def start_monitoring(self):
        """开始监控"""
        if self.running:
            logger.warning("GPU监控已在运行")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("GPU监控服务已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("GPU监控服务已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self._collect_metrics()
                self._check_alerts()
                self._cleanup_old_data()
                time.sleep(self.monitor_interval)
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                time.sleep(10)  # 出错时等待10秒再继续
    
    def _collect_metrics(self):
        """收集性能指标"""
        try:
            timestamp = datetime.now().isoformat()
            
            # 获取GPU状态
            gpu_status = TranslatorSingleton.get_gpu_status()
            
            # 获取系统信息
            system_info = self._get_system_info()
            
            # 获取NVIDIA GPU信息
            nvidia_info = self._get_nvidia_info()
            
            # 合并所有指标
            metrics = {
                "timestamp": timestamp,
                "gpu_status": gpu_status,
                "system_info": system_info,
                "nvidia_info": nvidia_info
            }
            
            # 存储指标
            self.performance_data.append(metrics)
            
            # 限制数据点数量
            if len(self.performance_data) > self.max_data_points:
                self.performance_data = self.performance_data[-self.max_data_points:]
            
            logger.debug(f"收集性能指标完成: {timestamp}")
            
        except Exception as e:
            logger.error(f"收集性能指标失败: {e}")
    
    def _get_system_info(self):
        """获取系统信息"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {}
    
    def _get_nvidia_info(self):
        """获取NVIDIA GPU信息"""
        try:
            # 检查CTranslate2 CUDA支持
            if not (hasattr(ctranslate2, 'cuda') and hasattr(ctranslate2.cuda, 'get_device_count')):
                logger.warning("CTranslate2 CUDA不可用，跳过GPU监控")
                return {"error": "CTranslate2 CUDA不可用"}
            
            gpu_count = ctranslate2.cuda.get_device_count()
            gpu_info = []
            
            for gpu_id in range(gpu_count):
                try:
                    memory_info = ctranslate2.cuda.get_device_memory_info(gpu_id)
                    gpu_info.append({
                        "gpu_id": gpu_id,
                        "total_memory": memory_info.total,
                        "free_memory": memory_info.free,
                        "used_memory": memory_info.total - memory_info.free,
                        "memory_percent": ((memory_info.total - memory_info.free) / memory_info.total) * 100
                    })
                except Exception as e:
                    logger.warning(f"获取GPU {gpu_id} 信息失败: {e}")
                    gpu_info.append({"gpu_id": gpu_id, "error": str(e)})
            
            return {
                "gpu_count": gpu_count,
                "gpu_details": gpu_info
            }
            
        except Exception as e:
            logger.error(f"获取NVIDIA GPU信息失败: {e}")
            return {"error": str(e)}
    
    def _check_alerts(self):
        """检查告警条件"""
        try:
            if not self.performance_data:
                return
            
            latest_metrics = self.performance_data[-1]
            
            # 检查GPU内存使用率
            if "nvidia_info" in latest_metrics and "gpu_details" in latest_metrics["nvidia_info"]:
                for gpu in latest_metrics["nvidia_info"]["gpu_details"]:
                    if "memory_percent" in gpu and gpu["memory_percent"] > self.memory_threshold:
                        logger.warning(f"GPU {gpu['gpu_id']} 内存使用率过高: {gpu['memory_percent']:.1f}%")
            
            # 检查系统资源
            if "system_info" in latest_metrics:
                sys_info = latest_metrics["system_info"]
                if sys_info.get("cpu_percent", 0) > 90:
                    logger.warning(f"CPU使用率过高: {sys_info['cpu_percent']:.1f}%")
                if sys_info.get("memory_percent", 0) > 90:
                    logger.warning(f"内存使用率过高: {sys_info['memory_percent']:.1f}%")
                if sys_info.get("disk_percent", 0) > 90:
                    logger.warning(f"磁盘使用率过高: {sys_info['disk_percent']:.1f}%")
            
            # 检查翻译服务状态
            if "gpu_status" in latest_metrics:
                gpu_status = latest_metrics["gpu_status"]
                if "performance_metrics" in gpu_status:
                    perf_metrics = gpu_status["performance_metrics"]
                    if perf_metrics.get("overall_success_rate", 1.0) < 0.95:
                        logger.warning(f"翻译服务成功率过低: {perf_metrics['overall_success_rate']:.2%}")
                    
        except Exception as e:
            logger.error(f"检查告警条件失败: {e}")
    
    def _cleanup_old_data(self):
        """清理旧数据"""
        try:
            if len(self.performance_data) > self.max_data_points:
                # 保留最近的数据点
                self.performance_data = self.performance_data[-self.max_data_points:]
                logger.debug(f"清理旧数据，保留 {self.max_data_points} 个数据点")
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
    
    def get_comprehensive_status(self):
        """获取综合状态信息"""
        try:
            if not self.performance_data:
                return {"error": "没有可用的性能数据"}
            
            latest_metrics = self.performance_data[-1]
            
            # 计算统计信息
            if len(self.performance_data) > 1:
                # 计算趋势
                recent_data = self.performance_data[-10:]  # 最近10个数据点
                cpu_trend = self._calculate_trend([d.get("system_info", {}).get("cpu_percent", 0) for d in recent_data])
                memory_trend = self._calculate_trend([d.get("system_info", {}).get("memory_percent", 0) for d in recent_data])
                
                status = {
                    "current_status": latest_metrics,
                    "trends": {
                        "cpu_trend": cpu_trend,
                        "memory_trend": memory_trend
                    },
                    "data_points": len(self.performance_data),
                    "monitoring_duration": self._calculate_monitoring_duration(),
                    "alerts": self._get_active_alerts()
                }
            else:
                status = {
                    "current_status": latest_metrics,
                    "data_points": len(self.performance_data),
                    "monitoring_duration": self._calculate_monitoring_duration()
                }
            
            return status
            
        except Exception as e:
            logger.error(f"获取综合状态失败: {e}")
            return {"error": str(e)}
    
    def _calculate_trend(self, values):
        """计算趋势（上升/下降/稳定）"""
        if len(values) < 2:
            return "stable"
        
        # 计算线性回归斜率
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * val for i, val in enumerate(values))
        x2_sum = sum(i * i for i in range(n))
        
        try:
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            if slope > 0.5:
                return "increasing"
            elif slope < -0.5:
                return "decreasing"
            else:
                return "stable"
        except ZeroDivisionError:
            return "stable"
    
    def _calculate_monitoring_duration(self):
        """计算监控持续时间"""
        if not self.performance_data:
            return 0
        
        start_time = datetime.fromisoformat(self.performance_data[0]["timestamp"])
        end_time = datetime.fromisoformat(self.performance_data[-1]["timestamp"])
        duration = end_time - start_time
        
        return {
            "seconds": duration.total_seconds(),
            "minutes": duration.total_seconds() / 60,
            "hours": duration.total_seconds() / 3600
        }
    
    def _get_active_alerts(self):
        """获取活跃告警"""
        alerts = []
        
        if not self.performance_data:
            return alerts
        
        latest_metrics = self.performance_data[-1]
        
        # 检查GPU内存告警
        if "nvidia_info" in latest_metrics and "gpu_details" in latest_metrics["nvidia_info"]:
            for gpu in latest_metrics["nvidia_info"]["gpu_details"]:
                if "memory_percent" in gpu and gpu["memory_percent"] > self.memory_threshold:
                    alerts.append({
                        "type": "gpu_memory_high",
                        "gpu_id": gpu["gpu_id"],
                        "value": gpu["memory_percent"],
                        "threshold": self.memory_threshold,
                        "severity": "warning"
                    })
        
        # 检查系统资源告警
        if "system_info" in latest_metrics:
            sys_info = latest_metrics["system_info"]
            if sys_info.get("cpu_percent", 0) > 90:
                alerts.append({
                    "type": "cpu_high",
                    "value": sys_info["cpu_percent"],
                    "threshold": 90,
                    "severity": "warning"
                })
            if sys_info.get("memory_percent", 0) > 90:
                alerts.append({
                    "type": "memory_high",
                    "value": sys_info["memory_percent"],
                    "threshold": 90,
                    "severity": "warning"
                })
        
        return alerts
    
    def export_metrics(self, filepath=None):
        """导出性能指标到文件"""
        try:
            if filepath is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = f"logs/gpu_metrics_{timestamp}.json"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.performance_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"性能指标已导出到: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"导出性能指标失败: {e}")
            return None


def main():
    """主函数"""
    try:
        # 创建GPU监控器
        monitor = GPUMonitor()
        
        # 启动监控
        monitor.start_monitoring()
        
        # 保持运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止监控...")
        finally:
            monitor.stop_monitoring()
            
    except Exception as e:
        logger.error(f"GPU监控服务运行失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
