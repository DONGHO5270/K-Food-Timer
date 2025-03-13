#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
타이머 기능을 관리하는 모듈
"""

import time
import threading
import datetime

from modules.utils import format_time

class Timer:
    """타이머 클래스"""
    
    def __init__(self, duration, name, callback=None):
        """타이머 초기화
        
        Args:
            duration (int): 타이머 지속 시간(초)
            name (str): 타이머 이름
            callback (function, optional): 타이머 완료 시 호출될 콜백 함수
        """
        self.duration = duration
        self.name = name
        self.callback = callback
        self.remaining = duration
        self.start_time = None
        self.is_running = False
        self.is_paused = False
        self.thread = None
    
    def start(self):
        """타이머 시작"""
        if self.is_running:
            return False
            
        self.is_running = True
        self.is_paused = False
        self.start_time = time.time()
        
        # 타이머 스레드 시작
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        
        return True
    
    def _run(self):
        """타이머 내부 실행 함수"""
        while self.is_running and self.remaining > 0:
            if not self.is_paused:
                time.sleep(0.1)  # 0.1초 단위로 업데이트
                elapsed = time.time() - self.start_time
                self.remaining = max(0, self.duration - int(elapsed))
                
                if self.remaining <= 0:
                    self.is_running = False
                    if self.callback:
                        self.callback(self)
                    break
            else:
                time.sleep(0.1)  # 일시정지 상태에서도 스레드 유지
    
    def pause(self):
        """타이머 일시정지"""
        if not self.is_running or self.is_paused:
            return False
            
        self.is_paused = True
        # 남은 시간 계산
        elapsed = time.time() - self.start_time
        self.remaining = max(0, self.duration - int(elapsed))
        return True
    
    def resume(self):
        """타이머 재개"""
        if not self.is_running or not self.is_paused:
            return False
            
        self.is_paused = False
        self.start_time = time.time() - (self.duration - self.remaining)
        return True
    
    def stop(self):
        """타이머 중지"""
        self.is_running = False
        self.is_paused = False
        return True
    
    def get_remaining_time(self):
        """남은 시간 반환 (초)"""
        if not self.is_running:
            return self.remaining
            
        if self.is_paused:
            return self.remaining
            
        elapsed = time.time() - self.start_time
        return max(0, self.duration - int(elapsed))
    
    def get_formatted_time(self):
        """형식화된 남은 시간 문자열 반환"""
        return format_time(self.get_remaining_time())
    
    def get_progress_percentage(self):
        """진행률 반환 (0-100%)"""
        if self.duration == 0:
            return 100
        return 100 - (self.get_remaining_time() * 100 // self.duration)


class TimerManager:
    """타이머 관리 클래스"""
    
    def __init__(self):
        """타이머 관리자 초기화"""
        self.timers = {}  # 타이머 ID를 키로 사용하는 딕셔너리
        self.next_id = 1
        self.notification_manager = None
        
    def set_notification_manager(self, notification_manager):
        """알림 관리자 설정
        
        Args:
            notification_manager: 알림 관리자 인스턴스
        """
        self.notification_manager = notification_manager
        
    def create_timer(self, duration, name):
        """새 타이머 생성
        
        Args:
            duration (int): 타이머 지속 시간(초)
            name (str): 타이머 이름
            
        Returns:
            int: 생성된 타이머의 ID
        """
        timer_id = self.next_id
        self.next_id += 1
        
        # 타이머 완료 콜백 함수
        def timer_complete_callback(timer):
            if self.notification_manager:
                self.notification_manager.notify("타이머 완료", f"{timer.name} 타이머가 완료되었습니다.")
        
        # 타이머 생성
        timer = Timer(duration, name, callback=timer_complete_callback)
        self.timers[timer_id] = timer
        
        return timer_id
    
    def start_timer(self, timer_id):
        """타이머 시작
        
        Args:
            timer_id (int): 타이머 ID
            
        Returns:
            bool: 성공 여부
        """
        timer = self.timers.get(timer_id)
        if not timer:
            return False
        return timer.start()
    
    def pause_timer(self, timer_id):
        """타이머 일시정지
        
        Args:
            timer_id (int): 타이머 ID
            
        Returns:
            bool: 성공 여부
        """
        timer = self.timers.get(timer_id)
        if not timer:
            return False
        return timer.pause()
    
    def resume_timer(self, timer_id):
        """타이머 재개
        
        Args:
            timer_id (int): 타이머 ID
            
        Returns:
            bool: 성공 여부
        """
        timer = self.timers.get(timer_id)
        if not timer:
            return False
        return timer.resume()
    
    def stop_timer(self, timer_id):
        """타이머 중지
        
        Args:
            timer_id (int): 타이머 ID
            
        Returns:
            bool: 성공 여부
        """
        timer = self.timers.get(timer_id)
        if not timer:
            return False
        return timer.stop()
    
    def delete_timer(self, timer_id):
        """타이머 삭제
        
        Args:
            timer_id (int): 타이머 ID
            
        Returns:
            bool: 성공 여부
        """
        if timer_id not in self.timers:
            return False
            
        timer = self.timers[timer_id]
        timer.stop()
        del self.timers[timer_id]
        return True
    
    def get_timer(self, timer_id):
        """타이머 객체 반환
        
        Args:
            timer_id (int): 타이머 ID
            
        Returns:
            Timer: 타이머 객체 또는 None
        """
        return self.timers.get(timer_id)
    
    def get_all_timers(self):
        """모든 타이머 반환
        
        Returns:
            dict: 타이머 ID를 키로 하는 타이머 딕셔너리
        """
        return self.timers
    
    def get_active_timers(self):
        """활성 타이머 반환
        
        Returns:
            dict: 활성 타이머 ID를 키로 하는 타이머 딕셔너리
        """
        return {tid: timer for tid, timer in self.timers.items() if timer.is_running} 