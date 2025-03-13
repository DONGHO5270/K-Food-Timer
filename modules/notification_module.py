#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K-Food Timer 애플리케이션의 알림 관리 모듈

이 모듈은 타이머 완료 시 사용자에게 알림을 보내는 기능을 담당합니다.
소리, 화면 메시지 등 다양한 알림 방식을 관리합니다.
"""

import sys
import platform
import threading
from time import sleep

from modules.utils import play_sound

class NotificationManager:
    """알림 관리 클래스"""
    
    def __init__(self, settings_manager):
        """알림 관리자 초기화
        
        Args:
            settings_manager: 설정 관리자 인스턴스 (의존성 주입)
        """
        self.settings_manager = settings_manager
        
    def notify(self, title, message):
        """알림 생성
        
        Args:
            title (str): 알림 제목
            message (str): 알림 메시지
        """
        # 콘솔에 메시지 출력
        self._show_console_message(title, message)
        
        # 소리 알림 (설정에 따라)
        if self.settings_manager.get_setting("sound_enabled", True):
            self._play_notification_sound()
            
        # 시스템 알림 (설정에 따라)
        if self.settings_manager.get_setting("notification_enabled", True):
            self._show_system_notification(title, message)
    
    def _show_console_message(self, title, message):
        """콘솔에 알림 메시지 출력
        
        Args:
            title (str): 알림 제목
            message (str): 알림 메시지
        """
        print("\n" + "!" * 50)
        print(f"{title}")
        print(f"{message}")
        print("!" * 50)
        
    def _play_notification_sound(self):
        """알림 소리 재생"""
        sound_thread = threading.Thread(target=play_sound)
        sound_thread.daemon = True
        sound_thread.start()
        
    def _show_system_notification(self, title, message):
        """시스템 알림 표시 (운영체제별 처리)
        
        Args:
            title (str): 알림 제목
            message (str): 알림 메시지
        """
        try:
            system = platform.system()
            
            if system == "Windows":
                # Windows Toast 알림 (필요한 경우 설치)
                self._show_windows_notification(title, message)
            elif system == "Darwin":  # macOS
                # AppleScript 사용
                self._show_macos_notification(title, message)
            elif system == "Linux":
                # notify-send 사용 (설치 필요)
                self._show_linux_notification(title, message)
                
        except Exception as e:
            print(f"시스템 알림 표시 중 오류 발생: {e}")
            
    def _show_windows_notification(self, title, message):
        """Windows 시스템 알림 표시
        
        Args:
            title (str): 알림 제목
            message (str): 알림 메시지
        """
        try:
            # 가벼운 Windows 알림 구현
            import ctypes
            ctypes.windll.user32.MessageBeep(0)
        except:
            pass
            
    def _show_macos_notification(self, title, message):
        """macOS 시스템 알림 표시
        
        Args:
            title (str): 알림 제목
            message (str): 알림 메시지
        """
        try:
            # osascript를 사용한 간단한 알림
            import os
            os.system(f"""osascript -e 'display notification "{message}" with title "{title}"'""")
        except:
            pass
            
    def _show_linux_notification(self, title, message):
        """Linux 시스템 알림 표시
        
        Args:
            title (str): 알림 제목
            message (str): 알림 메시지
        """
        try:
            # notify-send 사용
            import os
            os.system(f"""notify-send "{title}" "{message}" """)
        except:
            pass 