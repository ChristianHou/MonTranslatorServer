# config_manager.py
import configparser
import os
import logging
from typing import Any, Optional, Union, Dict, List
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


class ConfigManager:
    def __init__(self, config_file: str = "config/config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._load_config()
        self._validate_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_file):
                raise FileNotFoundError(f"配置文件不存在: {self.config_file}")
            
            self.config.read(self.config_file, encoding='utf-8')
            logger.info(f"配置文件加载成功: {self.config_file}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise ConfigValidationError(f"配置文件加载失败: {e}")
    
    def _validate_config(self) -> None:
        """验证配置的有效性"""
        try:
            self._validate_required_sections()
            self._validate_settings()
            self._validate_paths()
            self._validate_numeric_values()
            logger.info("配置验证通过")
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            raise ConfigValidationError(f"配置验证失败: {e}")
    
    def _validate_required_sections(self) -> None:
        """验证必需的配置节"""
        required_sections = ['SETTINGS', 'PATHS', 'LOGGING']
        for section in required_sections:
            if not self.config.has_section(section):
                raise ConfigValidationError(f"缺少必需的配置节: {section}")
    
    def _validate_settings(self) -> None:
        """验证SETTINGS节的关键配置"""
        settings = self.config['SETTINGS']
        
        # 验证必需键
        required_keys = ['MAX_TASKS', 'MAX_FILE_SIZE', 'SUPPORTED_LANGUAGES']
        for key in required_keys:
            if not settings.get(key):
                raise ConfigValidationError(f"缺少必需的配置键: {key}")
        
        # 验证语言配置
        languages = settings.get('SUPPORTED_LANGUAGES', '')
        if languages:
            valid_languages = ['eng_Latn', 'cmn_Hans', 'cmn_Hant', 'mon_Cyrl', 'mon_Mong']
            config_languages = [lang.strip() for lang in languages.split(',')]
            for lang in config_languages:
                if lang not in valid_languages:
                    raise ConfigValidationError(f"不支持的语言: {lang}")
    
    def _validate_paths(self) -> None:
        """验证路径配置"""
        paths = self.config['PATHS']
        
        # 验证模型路径
        model_path = paths.get('MODEL_PATH', '')
        if model_path and not os.path.exists(model_path):
            logger.warning(f"模型路径不存在: {model_path}")
        
        # 验证上传和下载目录
        upload_dir = paths.get('UPLOAD_DIRECTORY', '')
        download_dir = paths.get('DOWNLOAD_DIRECTORY', '')
        
        for path_name, path_value in [('上传目录', upload_dir), ('下载目录', download_dir)]:
            if path_value:
                try:
                    # 尝试创建目录（如果不存在）
                    os.makedirs(path_value, exist_ok=True)
                    # 检查目录权限
                    if not os.access(path_value, os.W_OK):
                        raise ConfigValidationError(f"{path_name}没有写权限: {path_value}")
                except Exception as e:
                    raise ConfigValidationError(f"{path_name}配置错误: {path_value}, 错误: {e}")
    
    def _validate_numeric_values(self) -> None:
        """验证数值配置"""
        settings = self.config['SETTINGS']
        
        # 验证MAX_TASKS
        try:
            max_tasks = int(settings.get('MAX_TASKS', '10'))
            if max_tasks <= 0 or max_tasks > 1000:
                raise ConfigValidationError(f"MAX_TASKS值无效: {max_tasks}, 应在1-1000之间")
        except ValueError:
            raise ConfigValidationError(f"MAX_TASKS必须是有效整数: {settings.get('MAX_TASKS')}")
        
        # 验证MAX_FILE_SIZE
        try:
            max_file_size = int(settings.get('MAX_FILE_SIZE', '10485760'))
            if max_file_size <= 0 or max_file_size > 1073741824:  # 1GB
                raise ConfigValidationError(f"MAX_FILE_SIZE值无效: {max_file_size}, 应在1字节-1GB之间")
        except ValueError:
            raise ConfigValidationError(f"MAX_FILE_SIZE必须是有效整数: {settings.get('MAX_FILE_SIZE')}")
    
    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """获取配置值，带验证"""
        try:
            if not self.config.has_section(section):
                logger.warning(f"配置节不存在: {section}")
                return fallback
            
            value = self.config.get(section, key, fallback=fallback)
            if value is None:
                logger.warning(f"配置键不存在: {section}.{key}")
                return fallback
            
            return value
            
        except Exception as e:
            logger.error(f"获取配置失败: {section}.{key}, 错误: {e}")
            return fallback
    
    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """获取整数配置值，带验证"""
        try:
            value = self.get(section, key, str(fallback))
            return int(value)
        except (ValueError, TypeError) as e:
            logger.error(f"配置值转换失败: {section}.{key}={value}, 错误: {e}")
            return fallback
    
    def getfloat(self, section: str, key: str, fallback: float = 0.0) -> float:
        """获取浮点数配置值，带验证"""
        try:
            value = self.get(section, key, str(fallback))
            return float(value)
        except (ValueError, TypeError) as e:
            logger.error(f"配置值转换失败: {section}.{key}={value}, 错误: {e}")
            return fallback
    
    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """获取布尔配置值，带验证"""
        try:
            value = self.get(section, key, str(fallback))
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)
        except Exception as e:
            logger.error(f"配置值转换失败: {section}.{key}={value}, 错误: {e}")
            return fallback
    
    def getlist(self, section: str, key: str, fallback: List[str] = None) -> List[str]:
        """获取列表配置值，带验证"""
        try:
            value = self.get(section, key, '')
            if not value:
                return fallback or []
            
            # 分割并清理列表值
            items = [item.strip() for item in value.split(',') if item.strip()]
            return items
            
        except Exception as e:
            logger.error(f"配置值转换失败: {section}.{key}={value}, 错误: {e}")
            return fallback or []
    
    def set(self, section: str, key: str, value: Any) -> None:
        """设置配置值，带验证"""
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)
            
            # 验证值类型
            if isinstance(value, (int, float, bool)):
                value = str(value)
            elif not isinstance(value, str):
                raise ValueError(f"不支持的配置值类型: {type(value)}")
            
            self.config.set(section, key, value)
            logger.info(f"配置值设置成功: {section}.{key}={value}")
            
        except Exception as e:
            logger.error(f"设置配置失败: {section}.{key}={value}, 错误: {e}")
            raise ConfigValidationError(f"设置配置失败: {e}")
    
    def save(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            logger.info(f"配置文件保存成功: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise ConfigValidationError(f"保存配置文件失败: {e}")
    
    def reload(self) -> None:
        """重新加载配置文件"""
        try:
            self._load_config()
            self._validate_config()
            logger.info("配置文件重新加载成功")
        except Exception as e:
            logger.error(f"重新加载配置文件失败: {e}")
            raise ConfigValidationError(f"重新加载配置文件失败: {e}")
    
    def get_model_path(self, model_name: str) -> str:
        """获取模型路径，带验证"""
        try:
            # 首先尝试从MODEL_LIST节获取模型路径
            if self.config.has_section('MODEL_LIST'):
                model_path = self.config.get('MODEL_LIST', model_name, fallback=None)
                if model_path:
                    # 检查路径是否存在
                    if os.path.exists(model_path):
                        logger.info(f"从MODEL_LIST获取模型路径: {model_path}")
                        return model_path
                    else:
                        logger.warning(f"MODEL_LIST中的路径不存在: {model_path}")
            
            # 如果MODEL_LIST中没有找到，则使用传统方法
            base_path = self.get('PATHS', 'MODEL_PATH', '')
            if not base_path:
                raise ConfigValidationError("MODEL_PATH未配置")
            
            model_path = os.path.join(base_path, model_name)
            if not os.path.exists(model_path):
                raise ConfigValidationError(f"模型路径不存在: {model_path}")
            
            return model_path
            
        except Exception as e:
            logger.error(f"获取模型路径失败: {model_name}, 错误: {e}")
            raise ConfigValidationError(f"获取模型路径失败: {e}")
    
    def get_upload_directory(self) -> str:
        """获取上传目录，带验证"""
        upload_dir = self.get('PATHS', 'UPLOAD_DIRECTORY', 'files/upload')
        try:
            os.makedirs(upload_dir, exist_ok=True)
            return upload_dir
        except Exception as e:
            logger.error(f"创建上传目录失败: {upload_dir}, 错误: {e}")
            raise ConfigValidationError(f"上传目录配置错误: {e}")
    
    def get_download_directory(self) -> str:
        """获取下载目录，带验证"""
        download_dir = self.get('PATHS', 'DOWNLOAD_DIRECTORY', 'files/download')
        try:
            os.makedirs(download_dir, exist_ok=True)
            return download_dir
        except Exception as e:
            logger.error(f"创建下载目录失败: {download_dir}, 错误: {e}")
            raise ConfigValidationError(f"下载目录配置错误: {e}")
    
    def validate_file_size(self, file_size: int) -> bool:
        """验证文件大小是否在允许范围内"""
        max_size = self.getint('SETTINGS', 'MAX_FILE_SIZE', 10485760)  # 默认10MB
        return file_size <= max_size
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return self.getlist('SETTINGS', 'SUPPORTED_LANGUAGES', ['eng_Latn', 'cmn_Hans'])
    
    def is_language_supported(self, language: str) -> bool:
        """检查语言是否支持"""
        supported = self.get_supported_languages()
        return language in supported


# 创建全局配置管理器实例
config_manager = ConfigManager()
