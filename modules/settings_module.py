#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
앱 설정을 관리하는 모듈
"""

import os
import json

class SettingsManager:
    """설정 관리 클래스"""
    
    def __init__(self, settings_path="data/settings.json"):
        """설정 관리자 초기화
        
        Args:
            settings_path (str, optional): 설정 파일 경로
        """
        self.settings_path = settings_path
        self.settings = {
            "sound_enabled": True,
            "notification_enabled": True,
            "theme": "light",
            "language": "ko",
            "auto_start": False,
            "timer_sound": "default",
            "recent_products": []
        }
    
    def load_settings(self):
        """설정 파일에서 설정 로드"""
        if not os.path.exists(self.settings_path):
            self._create_default_settings()
            return
            
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 기존 설정에 추가된 새 설정 항목이 있으면 병합
            for key, value in data.items():
                if key in self.settings:
                    self.settings[key] = value
                    
            print("설정을 로드했습니다.")
        except Exception as e:
            print(f"설정 로드 중 오류 발생: {e}")
            self._create_default_settings()
    
    def save_settings(self):
        """설정을 파일에 저장"""
        try:
            # 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
                
            print("설정을 저장했습니다.")
        except Exception as e:
            print(f"설정 저장 중 오류 발생: {e}")
    
    def _create_default_settings(self):
        """기본 설정 파일 생성"""
        try:
            self.save_settings()
            print("기본 설정 파일을 생성했습니다.")
        except Exception as e:
            print(f"기본 설정 파일 생성 중 오류 발생: {e}")
    
    def get_setting(self, key, default=None):
        """설정 값 조회
        
        Args:
            key (str): 설정 키
            default (any, optional): 설정이 없을 경우 반환할 기본값
            
        Returns:
            any: 설정 값 또는 기본값
        """
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        """설정 값 변경
        
        Args:
            key (str): 설정 키
            value (any): 설정 값
            
        Returns:
            bool: 설정 변경 성공 여부
        """
        if key in self.settings:
            self.settings[key] = value
            return True
        return False
    
    def update_settings(self, settings_dict):
        """여러 설정 값 한 번에 업데이트
        
        Args:
            settings_dict (dict): 업데이트할 설정 키-값 쌍
            
        Returns:
            bool: 업데이트 성공 여부
        """
        updated = False
        for key, value in settings_dict.items():
            if key in self.settings:
                self.settings[key] = value
                updated = True
        return updated
    
    def reset_to_defaults(self):
        """모든 설정을 기본값으로 초기화"""
        self.settings = {
            "sound_enabled": True,
            "notification_enabled": True,
            "theme": "light",
            "language": "ko",
            "auto_start": False,
            "timer_sound": "default",
            "recent_products": []
        }
        return True
    
    def add_recent_product(self, product_id, max_recent=10):
        """최근 사용한 제품 목록에 제품 추가
        
        Args:
            product_id (str): 제품 ID
            max_recent (int, optional): 최근 사용 목록 최대 크기
            
        Returns:
            bool: 추가 성공 여부
        """
        recent_products = self.settings.get("recent_products", [])
        
        # 이미 목록에 있으면 제거 (맨 앞으로 다시 추가하기 위해)
        if product_id in recent_products:
            recent_products.remove(product_id)
            
        # 목록 맨 앞에 추가
        recent_products.insert(0, product_id)
        
        # 최대 크기 초과 시 오래된 항목 제거
        if len(recent_products) > max_recent:
            recent_products = recent_products[:max_recent]
            
        self.settings["recent_products"] = recent_products
        return True
    
    def get_recent_products(self, limit=5):
        """최근 사용한 제품 ID 목록 반환
        
        Args:
            limit (int, optional): 반환할 제품 수
            
        Returns:
            list: 최근 사용한 제품 ID 목록
        """
        recent_products = self.settings.get("recent_products", [])
        return recent_products[:limit] 