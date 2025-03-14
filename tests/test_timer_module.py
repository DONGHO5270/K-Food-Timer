#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
타이머 모듈 테스트 스크립트

Timer, TimerQueue, StepTimer 클래스의 기능을 테스트합니다.
"""

import os
import sys
import unittest
import time
from unittest.mock import MagicMock

# 상위 디렉토리를 시스템 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.timer_module import Timer, TimerQueue, StepTimer, TimerStatus, TimerNotification, TimerStorage

class TestTimer(unittest.TestCase):
    """Timer 클래스 테스트"""
    
    def test_timer_creation(self):
        """타이머 생성 테스트"""
        timer = Timer("product_1", "테스트 제품", 60)
        self.assertEqual(timer.product_id, "product_1")
        self.assertEqual(timer.product_name, "테스트 제품")
        self.assertEqual(timer.duration, 60)
        self.assertEqual(timer.status, TimerStatus.READY)
    
    def test_timer_start_pause_resume(self):
        """타이머 시작, 일시정지, 재개 테스트"""
        timer = Timer("product_1", "테스트 제품", 60)
        
        # 타이머 시작
        result = timer.start()
        self.assertTrue(result)
        self.assertEqual(timer.status, TimerStatus.RUNNING)
        
        # 잠시 대기 후 남은 시간 확인
        time.sleep(0.5)
        self.assertLess(timer.get_remaining_time(), 60)
        
        # 타이머 일시정지
        result = timer.pause()
        self.assertTrue(result)
        self.assertEqual(timer.status, TimerStatus.PAUSED)
        
        # 일시정지 시 남은 시간 기록
        paused_time = timer.get_remaining_time()
        
        # 잠시 대기 후 남은 시간 다시 확인 (변화 없어야 함)
        time.sleep(0.5)
        self.assertEqual(timer.get_remaining_time(), paused_time)
        
        # 타이머 재개
        result = timer.resume()
        self.assertTrue(result)
        self.assertEqual(timer.status, TimerStatus.RUNNING)
        
        # 재개 후 남은 시간 감소 확인
        time.sleep(0.5)
        self.assertLess(timer.get_remaining_time(), paused_time)
    
    def test_timer_cancel(self):
        """타이머 취소 테스트"""
        timer = Timer("product_1", "테스트 제품", 60)
        timer.start()
        
        # 타이머 취소
        result = timer.cancel()
        self.assertTrue(result)
        self.assertEqual(timer.status, TimerStatus.CANCELLED)
        
        # 취소 후 다시 시작 시도 (실패해야 함)
        result = timer.start()
        self.assertFalse(result)
    
    def test_timer_callbacks(self):
        """타이머 콜백 테스트"""
        # 콜백 모의 함수
        mock_callback = MagicMock()
        
        # 콜백이 있는 타이머 생성
        timer = Timer("product_1", "테스트 제품", 1, callback=mock_callback)
        
        # 타이머 시작
        timer.start()
        mock_callback.assert_called_with(timer.timer_id, TimerStatus.RUNNING)
        
        # 콜백 호출 횟수 초기화
        mock_callback.reset_mock()
        
        # 타이머 완료 대기 (1초 이상)
        time.sleep(1.5)
        
        # 타이머 완료 콜백 확인
        mock_callback.assert_called_with(timer.timer_id, TimerStatus.COMPLETED)
    
    def test_timer_to_dict_from_dict(self):
        """타이머 직렬화/역직렬화 테스트"""
        timer = Timer("product_1", "테스트 제품", 60)
        timer.start()
        
        # 타이머를 딕셔너리로 변환
        timer_dict = timer.to_dict()
        
        # 모든 필수 필드 존재 확인
        self.assertIn("timer_id", timer_dict)
        self.assertIn("product_id", timer_dict)
        self.assertIn("duration", timer_dict)
        self.assertIn("status", timer_dict)
        
        # 딕셔너리에서 타이머 복원
        loaded_timer = Timer.from_dict(timer_dict)
        
        # 속성 비교
        self.assertEqual(loaded_timer.timer_id, timer.timer_id)
        self.assertEqual(loaded_timer.product_id, timer.product_id)
        self.assertEqual(loaded_timer.product_name, timer.product_name)
        self.assertEqual(loaded_timer.duration, timer.duration)
        self.assertEqual(loaded_timer.status, timer.status)

class TestTimerQueue(unittest.TestCase):
    """TimerQueue 클래스 테스트"""
    
    def test_queue_creation_and_timer_addition(self):
        """타이머 큐 생성 및 타이머 추가 테스트"""
        queue = TimerQueue("테스트 큐")
        self.assertEqual(queue.name, "테스트 큐")
        self.assertEqual(len(queue.timers), 0)
        
        # 타이머 추가
        timer1 = Timer("product_1", "제품 1", 10)
        queue.add_timer(timer1)
        self.assertEqual(len(queue.timers), 1)
        
        # 제품 정보로 타이머 추가
        timer2 = queue.add_timer_from_product("product_2", "제품 2", 20)
        self.assertEqual(len(queue.timers), 2)
        self.assertEqual(timer2.product_id, "product_2")
        self.assertEqual(timer2.duration, 20)
    
    def test_queue_start_and_timer_progression(self):
        """타이머 큐 시작 및 타이머 진행 테스트"""
        queue = TimerQueue("테스트 큐")
        
        # 짧은 시간의 타이머 추가 (테스트 시간 단축)
        queue.add_timer_from_product("product_1", "제품 1", 1)
        queue.add_timer_from_product("product_2", "제품 2", 1)
        
        # 타이머 큐 시작
        result = queue.start()
        self.assertTrue(result)
        self.assertEqual(queue.status, TimerStatus.RUNNING)
        self.assertEqual(queue.current_index, 0)
        
        # 첫 번째 타이머가 실행 중인지 확인
        current_timer = queue.get_current_timer()
        self.assertIsNotNone(current_timer)
        self.assertEqual(current_timer.product_name, "제품 1")
        
        # 첫 번째 타이머 완료 및 두 번째 타이머로 자동 전환 대기
        time.sleep(1.5)
        
        # 두 번째 타이머가 실행 중인지 확인
        current_timer = queue.get_current_timer()
        self.assertIsNotNone(current_timer)
        self.assertEqual(current_timer.product_name, "제품 2")
        
        # 두 번째 타이머 완료 및 큐 완료 대기
        time.sleep(1.5)
        
        # 큐가 완료 상태인지 확인
        self.assertEqual(queue.status, TimerStatus.COMPLETED)
        self.assertEqual(queue.current_index, -1)

class TestStepTimer(unittest.TestCase):
    """StepTimer 클래스 테스트"""
    
    def test_step_timer_creation(self):
        """단계별 타이머 생성 테스트"""
        steps = [
            ("단계 1", 10),
            ("단계 2", 20),
            ("단계 3", 30)
        ]
        
        step_timer = StepTimer("product_1", "테스트 제품", steps)
        
        self.assertEqual(step_timer.product_id, "product_1")
        self.assertEqual(step_timer.product_name, "테스트 제품")
        self.assertEqual(len(step_timer.steps), 3)
        
        # 내부 타이머 큐 생성 확인
        self.assertEqual(len(step_timer.timer_queue.timers), 3)
    
    def test_step_timer_total_duration(self):
        """단계별 타이머 총 소요 시간 테스트"""
        steps = [
            ("단계 1", 10),
            ("단계 2", 20),
            ("단계 3", 30)
        ]
        
        step_timer = StepTimer("product_1", "테스트 제품", steps)
        
        # 총 소요 시간은 모든 단계의 합
        self.assertEqual(step_timer.get_total_duration(), 60)
    
    def test_step_timer_progression(self):
        """단계별 타이머 진행 테스트"""
        # 콜백 모의 함수
        mock_callback = MagicMock()
        
        steps = [
            ("단계 1", 1),
            ("단계 2", 1)
        ]
        
        step_timer = StepTimer("product_1", "테스트 제품", steps, callback=mock_callback)
        
        # 단계별 타이머 시작
        result = step_timer.start()
        self.assertTrue(result)
        
        # 시작 콜백 확인
        mock_callback.assert_called_with(step_timer.step_timer_id, 0, "단계 1", TimerStatus.RUNNING)
        
        # 첫 번째 단계 완료 및 두 번째 단계로 전환 대기
        time.sleep(1.5)
        
        # 두 번째 단계 진입 콜백 확인
        mock_callback.assert_called_with(step_timer.step_timer_id, 1, "단계 2", TimerStatus.RUNNING)
        
        # 두 번째 단계의 현재 상태 확인
        step_index, step_description, remaining_time = step_timer.get_current_step()
        self.assertEqual(step_index, 1)
        self.assertEqual(step_description, "단계 2")
        
        # 두 번째 단계 완료 및 타이머 완료 대기
        time.sleep(1.5)
        
        # 완료 콜백 확인
        mock_callback.assert_called_with(step_timer.step_timer_id, -1, "", TimerStatus.COMPLETED)

if __name__ == "__main__":
    unittest.main() 