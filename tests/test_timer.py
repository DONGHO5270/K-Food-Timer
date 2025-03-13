#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
타이머 모듈 테스트
"""

import unittest
import time
from modules.timer_module import Timer, TimerManager

class TestTimer(unittest.TestCase):
    """타이머 클래스 테스트"""
    
    def test_timer_init(self):
        """타이머 초기화 테스트"""
        timer = Timer(60, "테스트 타이머")
        self.assertEqual(timer.duration, 60)
        self.assertEqual(timer.name, "테스트 타이머")
        self.assertEqual(timer.remaining, 60)
        self.assertFalse(timer.is_running)
        self.assertFalse(timer.is_paused)
        
    def test_timer_start_stop(self):
        """타이머 시작/정지 테스트"""
        timer = Timer(60, "테스트 타이머")
        
        # 타이머 시작
        result = timer.start()
        self.assertTrue(result)
        self.assertTrue(timer.is_running)
        self.assertFalse(timer.is_paused)
        
        # 이미 실행 중인 타이머 시작 시도
        result = timer.start()
        self.assertFalse(result)
        
        # 타이머 정지
        result = timer.stop()
        self.assertTrue(result)
        self.assertFalse(timer.is_running)
        
        # 이미 정지된 타이머 정지 시도
        result = timer.stop()
        self.assertFalse(result)
        
    def test_timer_pause_resume(self):
        """타이머 일시정지/재개 테스트"""
        timer = Timer(60, "테스트 타이머")
        
        # 실행 중이지 않은 타이머 일시정지 시도
        result = timer.pause()
        self.assertFalse(result)
        
        # 타이머 시작
        timer.start()
        
        # 일시정지
        result = timer.pause()
        self.assertTrue(result)
        self.assertTrue(timer.is_paused)
        
        # 이미 일시정지된 타이머 일시정지 시도
        result = timer.pause()
        self.assertFalse(result)
        
        # 재개
        result = timer.resume()
        self.assertTrue(result)
        self.assertFalse(timer.is_paused)
        
        # 이미 실행 중인 타이머 재개 시도
        result = timer.resume()
        self.assertFalse(result)
        
        # 정지
        timer.stop()
        
    def test_timer_callback(self):
        """타이머 콜백 테스트"""
        callback_called = False
        
        def callback(timer):
            nonlocal callback_called
            callback_called = True
            self.assertEqual(timer.remaining, 0)
            
        # 짧은 시간의 타이머 생성
        timer = Timer(0.1, "테스트 타이머", callback)
        timer.start()
        
        # 타이머가 완료될 때까지 대기
        time.sleep(0.2)
        
        # 콜백이 호출되었는지 확인
        self.assertTrue(callback_called)
        
    def test_get_remaining_time(self):
        """남은 시간 반환 테스트"""
        timer = Timer(60, "테스트 타이머")
        
        # 시작 전
        self.assertEqual(timer.get_remaining_time(), 60)
        
        # 시작 후
        timer.start()
        time.sleep(0.1)
        remaining = timer.get_remaining_time()
        self.assertLess(remaining, 60)
        
        # 일시정지 후
        timer.pause()
        paused_remaining = timer.get_remaining_time()
        time.sleep(0.1)
        self.assertEqual(timer.get_remaining_time(), paused_remaining)
        
        # 재개 후
        timer.resume()
        time.sleep(0.1)
        self.assertLess(timer.get_remaining_time(), paused_remaining)
        
        # 정지 후
        timer.stop()
        
    def test_get_formatted_time(self):
        """포맷된 시간 테스트"""
        timer = Timer(65, "테스트 타이머")
        self.assertEqual(timer.get_formatted_time(), "01:05")
        
        timer = Timer(3600, "테스트 타이머")
        self.assertEqual(timer.get_formatted_time(), "60:00")


class TestTimerManager(unittest.TestCase):
    """타이머 관리자 테스트"""
    
    def setUp(self):
        """테스트 전 설정"""
        self.timer_manager = TimerManager()
        
    def test_create_timer(self):
        """타이머 생성 테스트"""
        timer, timer_id = self.timer_manager.create_timer(60, "테스트 타이머")
        
        self.assertIsNotNone(timer)
        self.assertIsNotNone(timer_id)
        self.assertEqual(timer.duration, 60)
        self.assertEqual(timer.name, "테스트 타이머")
        self.assertIn(timer_id, self.timer_manager.timers)
        
    def test_start_timer(self):
        """타이머 시작 테스트"""
        timer, timer_id = self.timer_manager.create_timer(60, "테스트 타이머")
        
        # 타이머 시작
        result = self.timer_manager.start_timer(timer_id)
        self.assertTrue(result)
        self.assertIn(timer_id, self.timer_manager.active_timers)
        
        # 존재하지 않는 타이머 ID로 시작 시도
        result = self.timer_manager.start_timer("non_existent_id")
        self.assertFalse(result)
        
    def test_pause_resume_timer(self):
        """타이머 일시정지/재개 테스트"""
        timer, timer_id = self.timer_manager.create_timer(60, "테스트 타이머")
        self.timer_manager.start_timer(timer_id)
        
        # 일시정지
        result = self.timer_manager.pause_timer(timer_id)
        self.assertTrue(result)
        self.assertTrue(timer.is_paused)
        
        # 재개
        result = self.timer_manager.resume_timer(timer_id)
        self.assertTrue(result)
        self.assertFalse(timer.is_paused)
        
        # 존재하지 않는 타이머 ID로 일시정지/재개 시도
        result = self.timer_manager.pause_timer("non_existent_id")
        self.assertFalse(result)
        result = self.timer_manager.resume_timer("non_existent_id")
        self.assertFalse(result)
        
    def test_stop_timer(self):
        """타이머 정지 테스트"""
        timer, timer_id = self.timer_manager.create_timer(60, "테스트 타이머")
        self.timer_manager.start_timer(timer_id)
        
        # 타이머 정지
        result = self.timer_manager.stop_timer(timer_id)
        self.assertTrue(result)
        self.assertFalse(timer.is_running)
        self.assertNotIn(timer_id, self.timer_manager.active_timers)
        
        # 존재하지 않는 타이머 ID로 정지 시도
        result = self.timer_manager.stop_timer("non_existent_id")
        self.assertFalse(result)
        
    def test_get_active_timers(self):
        """활성 타이머 목록 반환 테스트"""
        self.assertEqual(len(self.timer_manager.get_active_timers()), 0)
        
        timer1, timer_id1 = self.timer_manager.create_timer(60, "타이머1")
        timer2, timer_id2 = self.timer_manager.create_timer(120, "타이머2")
        
        self.timer_manager.start_timer(timer_id1)
        self.assertEqual(len(self.timer_manager.get_active_timers()), 1)
        
        self.timer_manager.start_timer(timer_id2)
        self.assertEqual(len(self.timer_manager.get_active_timers()), 2)
        
        self.timer_manager.stop_timer(timer_id1)
        self.assertEqual(len(self.timer_manager.get_active_timers()), 1)
        
        self.timer_manager.stop_timer(timer_id2)
        self.assertEqual(len(self.timer_manager.get_active_timers()), 0)
        
    def test_get_timer(self):
        """타이머 객체 반환 테스트"""
        timer, timer_id = self.timer_manager.create_timer(60, "테스트 타이머")
        
        retrieved_timer = self.timer_manager.get_timer(timer_id)
        self.assertEqual(retrieved_timer, timer)
        
        # 존재하지 않는 타이머 ID로 조회 시도
        self.assertIsNone(self.timer_manager.get_timer("non_existent_id"))


if __name__ == "__main__":
    unittest.main() 