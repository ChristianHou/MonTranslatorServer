#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控脚本
监控修复后的系统性能表现
"""

import time
import threading
import psutil
import os
import sys
from collections import defaultdict
import json
from datetime import datetime


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_time = time.time()
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("🔍 性能监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("⏹️ 性能监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # 收集系统指标
                self._collect_metrics()
                time.sleep(1)  # 每秒收集一次
            except Exception as e:
                print(f"监控错误: {e}")
    
    def _collect_metrics(self):
        """收集性能指标"""
        timestamp = time.time()
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.metrics['cpu_percent'].append({
            'timestamp': timestamp,
            'value': cpu_percent
        })
        
        # 内存使用
        memory = psutil.virtual_memory()
        self.metrics['memory_percent'].append({
            'timestamp': timestamp,
            'value': memory.percent
        })
        
        # 磁盘I/O
        disk_io = psutil.disk_io_counters()
        if disk_io:
            self.metrics['disk_read_bytes'].append({
                'timestamp': timestamp,
                'value': disk_io.read_bytes
            })
            self.metrics['disk_write_bytes'].append({
                'timestamp': timestamp,
                'value': disk_io.write_bytes
            })
        
        # 网络I/O
        network_io = psutil.net_io_counters()
        if network_io:
            self.metrics['network_bytes_sent'].append({
                'timestamp': timestamp,
                'value': network_io.bytes_sent
            })
            self.metrics['network_bytes_recv'].append({
                'timestamp': timestamp,
                'value': network_io.bytes_recv
            })
        
        # 进程数量
        process_count = len(psutil.pids())
        self.metrics['process_count'].append({
            'timestamp': timestamp,
            'value': process_count
        })
    
    def get_summary(self):
        """获取性能摘要"""
        summary = {}
        
        for metric_name, data in self.metrics.items():
            if data:
                values = [item['value'] for item in data]
                summary[metric_name] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'latest': values[-1] if values else None
                }
        
        return summary
    
    def save_metrics(self, filename=None):
        """保存指标到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"
        
        # 准备保存的数据
        save_data = {
            'monitor_start_time': self.start_time,
            'monitor_duration': time.time() - self.start_time,
            'summary': self.get_summary(),
            'raw_metrics': dict(self.metrics)
        }
        
        # 保存到文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        print(f"📊 性能指标已保存到: {filename}")
        return filename


class LoadTester:
    """负载测试器"""
    
    def __init__(self, monitor):
        self.monitor = monitor
        self.test_results = []
    
    def run_concurrent_test(self, num_threads, duration, test_func):
        """运行并发测试"""
        print(f"🚀 开始并发测试: {num_threads}个线程, 持续{duration}秒")
        
        # 启动监控
        self.monitor.start_monitoring()
        
        # 创建测试线程
        threads = []
        results = []
        start_time = time.time()
        
        def worker(thread_id):
            thread_results = []
            thread_start = time.time()
            
            while time.time() - thread_start < duration:
                try:
                    start = time.time()
                    result = test_func(thread_id)
                    end = time.time()
                    
                    thread_results.append({
                        'thread_id': thread_id,
                        'success': result,
                        'duration': end - start,
                        'timestamp': time.time()
                    })
                    
                    time.sleep(0.1)  # 避免过度频繁的请求
                    
                except Exception as e:
                    thread_results.append({
                        'thread_id': thread_id,
                        'success': False,
                        'error': str(e),
                        'timestamp': time.time()
                    })
            
            results.extend(thread_results)
        
        # 启动所有线程
        for i in range(num_threads):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 停止监控
        self.monitor.stop_monitoring()
        
        # 分析结果
        test_duration = time.time() - start_time
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r.get('success', False))
        failed_requests = total_requests - successful_requests
        
        if successful_requests > 0:
            avg_response_time = sum(r['duration'] for r in results if r.get('success', False)) / successful_requests
        else:
            avg_response_time = 0
        
        # 保存测试结果
        test_result = {
            'test_type': 'concurrent_test',
            'num_threads': num_threads,
            'duration': duration,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': successful_requests / total_requests if total_requests > 0 else 0,
            'avg_response_time': avg_response_time,
            'requests_per_second': total_requests / test_duration if test_duration > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results.append(test_result)
        
        # 打印结果
        print(f"📊 测试完成:")
        print(f"   总请求数: {total_requests}")
        print(f"   成功请求: {successful_requests}")
        print(f"   失败请求: {failed_requests}")
        print(f"   成功率: {test_result['success_rate']:.2%}")
        print(f"   平均响应时间: {avg_response_time:.3f}秒")
        print(f"   请求/秒: {test_result['requests_per_second']:.2f}")
        
        return test_result
    
    def save_test_results(self, filename=None):
        """保存测试结果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"load_test_results_{timestamp}.json"
        
        save_data = {
            'test_results': self.test_results,
            'monitor_summary': self.monitor.get_summary()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        print(f"📊 测试结果已保存到: {filename}")
        return filename


def simulate_translation_workload(thread_id):
    """模拟翻译工作负载"""
    # 模拟翻译处理时间
    processing_time = 0.1 + (thread_id % 3) * 0.05  # 0.1-0.2秒
    time.sleep(processing_time)
    
    # 模拟偶尔的失败
    if thread_id % 20 == 0:  # 5%的失败率
        raise Exception("模拟的翻译失败")
    
    return True


def main():
    """主函数"""
    print("🚀 蒙语翻译服务器性能监控和负载测试")
    print("=" * 60)
    
    # 创建性能监控器
    monitor = PerformanceMonitor()
    
    # 创建负载测试器
    load_tester = LoadTester(monitor)
    
    try:
        # 运行不同规模的并发测试
        test_scenarios = [
            (5, 10),   # 5个线程，10秒
            (10, 15),  # 10个线程，15秒
            (20, 20),  # 20个线程，20秒
        ]
        
        for num_threads, duration in test_scenarios:
            print(f"\n🔄 运行测试场景: {num_threads}线程 x {duration}秒")
            result = load_tester.run_concurrent_test(
                num_threads=num_threads,
                duration=duration,
                test_func=simulate_translation_workload
            )
            
            # 等待一段时间再进行下一个测试
            time.sleep(5)
        
        # 保存所有结果
        print("\n💾 保存测试结果...")
        test_results_file = load_tester.save_test_results()
        metrics_file = monitor.save_metrics()
        
        # 打印最终摘要
        print("\n📊 性能监控摘要:")
        summary = monitor.get_summary()
        for metric_name, data in summary.items():
            print(f"   {metric_name}:")
            print(f"     平均值: {data['avg']:.2f}")
            print(f"     最大值: {data['max']:.2f}")
            print(f"     最小值: {data['min']:.2f}")
        
        print(f"\n✅ 所有测试完成！")
        print(f"   测试结果: {test_results_file}")
        print(f"   性能指标: {metrics_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
    finally:
        # 确保监控被停止
        if monitor.monitoring:
            monitor.stop_monitoring()


if __name__ == "__main__":
    main()
