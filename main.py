#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K-Food Timer 애플리케이션의 메인 진입점
한국 간편식품의 조리 시간을 관리하는 타이머 앱
"""

import sys
import os
import json

# 모듈 import
from modules.timer_module import TimerManager
from modules.product_module import ProductManager
from modules.settings_module import SettingsManager
from modules.ui_module import UIManager
from modules.menu_module import MenuManager
from modules.notification_module import NotificationManager
from modules.utils import clear_screen

class KFoodTimerApp:
    """K-Food Timer 앱의 메인 클래스"""
    
    def __init__(self):
        """앱 초기화"""
        # 기본 관리자 모듈 초기화
        self.settings_manager = SettingsManager()
        self.product_manager = ProductManager()
        self.timer_manager = TimerManager()
        
        # UI 관련 모듈 초기화
        self.ui_manager = UIManager(self)
        
        # 의존성 주입 설정
        self.timer_manager.set_notification_manager(self.ui_manager.notification_manager)
        
    def run(self):
        """앱 실행"""
        print("K-Food Timer 앱을 시작합니다...")
        # 설정 로드
        self.settings_manager.load_settings()
        # 제품 데이터 로드
        self.product_manager.load_products()
        # UI 시작
        self.ui_manager.start()
        
    def exit(self):
        """앱 종료"""
        print("K-Food Timer 앱을 종료합니다...")
        # 설정 저장
        self.settings_manager.save_settings()
        # 제품 데이터 저장
        self.product_manager.save_products()
        sys.exit(0)

if __name__ == "__main__":
    app = KFoodTimerApp()
    try:
        app.run()
    except KeyboardInterrupt:
        app.exit()
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        app.exit() 