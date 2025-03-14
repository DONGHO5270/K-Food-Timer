#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
앱 설정을 관리하는 모듈
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class Settings:
    """설정 관리 클래스
    
    앱의 환경설정, 사용자 기본 설정 등을 관리합니다.
    """
    
    def __init__(self, settings_path: str = "data/settings.json"):
        """Settings 초기화
        
        Args:
            settings_path (str): 설정 파일 경로
        """
        self.settings_path = settings_path
        self.settings = self._get_default_settings()
        self._ensure_data_dir()
        
    def _ensure_data_dir(self) -> None:
        """데이터 디렉토리 존재 확인 및 생성"""
        data_dir = os.path.dirname(self.settings_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            logger.info(f"데이터 디렉토리 생성: {data_dir}")
            
    def _get_default_settings(self) -> Dict[str, Any]:
        """기본 설정값 반환
        
        Returns:
            dict: 기본 설정값
        """
        return {
            "sound_enabled": True,
            "desktop_notification": True,
            "language": "ko",
            "theme": "light",
            "recent_products": []
        }
        
    def load_settings(self) -> bool:
        """설정 로드
        
        Returns:
            bool: 로드 성공 여부
        """
        if not os.path.exists(self.settings_path):
            logger.info("설정 파일이 없습니다. 기본 설정을 사용합니다.")
            self.save_settings()
            return True
            
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                
            # 기본 설정을 기반으로 로드된 설정 업데이트
            default_settings = self._get_default_settings()
            for key, value in loaded_settings.items():
                if key in default_settings:
                    default_settings[key] = value
                    
            self.settings = default_settings
            logger.info("설정을 로드했습니다.")
            return True
        except Exception as e:
            logger.error(f"설정 로드 중 오류 발생: {e}")
            return False
            
    def save_settings(self) -> bool:
        """설정 저장
        
        Returns:
            bool: 저장 성공 여부
        """
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
                
            logger.info("설정을 저장했습니다.")
            return True
        except Exception as e:
            logger.error(f"설정 저장 중 오류 발생: {e}")
            return False
            
    def get_settings(self) -> Dict[str, Any]:
        """모든 설정 조회
        
        Returns:
            dict: 현재 설정값
        """
        return self.settings
        
    def get_setting(self, key: str, default: Any = None) -> Any:
        """특정 설정 조회
        
        Args:
            key (str): 설정 키
            default (Any, optional): 기본값
            
        Returns:
            Any: 설정값 또는 기본값
        """
        return self.settings.get(key, default)
        
    def set_setting(self, key: str, value: Any) -> None:
        """설정 변경
        
        Args:
            key (str): 설정 키
            value (Any): 설정값
        """
        self.settings[key] = value
        logger.info(f"설정 변경: {key} = {value}")
        
    def toggle_setting(self, key: str) -> bool:
        """불리언 설정 토글
        
        Args:
            key (str): 설정 키
            
        Returns:
            bool: 토글 후 설정값
        """
        if key in self.settings and isinstance(self.settings[key], bool):
            self.settings[key] = not self.settings[key]
            logger.info(f"설정 토글: {key} = {self.settings[key]}")
            return self.settings[key]
        return False
        
    def reset_settings(self) -> None:
        """모든 설정 초기화"""
        self.settings = self._get_default_settings()
        logger.info("설정을 초기화했습니다.")
        
    def add_recent_product(self, product_id: str, max_recent: int = 10) -> None:
        """최근 사용 제품 추가
        
        Args:
            product_id (str): 제품 ID
            max_recent (int, optional): 최대 저장 개수
        """
        recent = self.settings.get("recent_products", [])
        
        # 이미 있으면 제거 (나중에 맨 앞에 추가)
        if product_id in recent:
            recent.remove(product_id)
            
        # 맨 앞에 추가
        recent.insert(0, product_id)
        
        # 최대 개수 유지
        self.settings["recent_products"] = recent[:max_recent]
        logger.debug(f"최근 사용 제품 추가: {product_id}")
        
    def get_recent_product_ids(self, limit: int = 5) -> List[str]:
        """최근 사용 제품 ID 목록 조회
        
        Args:
            limit (int, optional): 최대 개수
            
        Returns:
            list: 최근 사용 제품 ID 목록
        """
        recent = self.settings.get("recent_products", [])
        return recent[:limit] 