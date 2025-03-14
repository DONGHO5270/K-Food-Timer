#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K-Food 타이머 애플리케이션의 타이머 모듈

이 모듈은 다음 클래스를 포함합니다:
- Timer: 기본 타이머 기능을 제공
- TimerQueue: 다중 타이머 관리
- StepTimer: 단계별 타이머 관리
- TimerNotification: 타이머 알림 관리
- TimerStorage: 타이머 상태 저장 및 불러오기
"""

import time
import threading
import json
import uuid
import os
import platform
import subprocess
import logging
from enum import Enum
from typing import List, Dict, Any, Callable, Optional, Tuple, Union
from pathlib import Path

from modules.utils import format_time

logger = logging.getLogger(__name__)

class TimerStatus(Enum):
    """타이머 상태를 나타내는 열거형 클래스"""
    READY = "ready"       # 준비 상태
    RUNNING = "running"   # 실행 중
    PAUSED = "paused"     # 일시정지
    COMPLETED = "completed" # 완료
    CANCELLED = "cancelled" # 취소됨

class Timer:
    """
    기본 타이머 클래스
    
    속성:
        timer_id (str): 타이머의 고유 ID
        product_id (str): 타이머에 연결된 제품 ID
        product_name (str): 제품 이름
        duration (int): 타이머 지속 시간(초)
        start_time (float): 타이머 시작 시간
        end_time (float): 타이머 종료 예정 시간
        paused_time (float): 타이머가 일시정지된 시간
        elapsed_pause_time (float): 일시정지에서 소요된 총 시간
        status (TimerStatus): 현재 타이머 상태
        callback (Callable): 타이머 상태 변경 시 호출될 콜백 함수
        timer_thread (threading.Thread): 타이머 스레드
        _stop_event (threading.Event): 타이머 중지 이벤트
    """
    
    def __init__(self, product_id: str, product_name: str, duration: int, 
                 callback: Optional[Callable[[str, TimerStatus], None]] = None):
        """
        타이머 객체 초기화
        
        Args:
            product_id (str): 타이머와 연결된 제품 ID
            product_name (str): 제품 이름
            duration (int): 타이머 지속 시간(초)
            callback (Callable, optional): 타이머 상태 변경 시 호출될 콜백 함수
        """
        self.timer_id = str(uuid.uuid4())
        self.product_id = product_id
        self.product_name = product_name
        self.duration = duration
        self.start_time = 0
        self.end_time = 0
        self.paused_time = 0
        self.elapsed_pause_time = 0
        self.status = TimerStatus.READY
        self.callback = callback
        self.timer_thread = None
        self._stop_event = threading.Event()
    
    def start(self) -> bool:
        """
        타이머 시작
        
        Returns:
            bool: 타이머 시작 성공 여부
        """
        if self.status != TimerStatus.READY and self.status != TimerStatus.PAUSED:
            return False
        
        if self.status == TimerStatus.READY:
            self.start_time = time.time()
            self.end_time = self.start_time + self.duration
            self.elapsed_pause_time = 0
        elif self.status == TimerStatus.PAUSED:
            # 일시정지 시간 계산
            pause_duration = time.time() - self.paused_time
            self.elapsed_pause_time += pause_duration
            # 종료 시간 재설정
            self.end_time += pause_duration
        
        self.status = TimerStatus.RUNNING
        self._stop_event.clear()
        
        # 콜백 호출
        if self.callback:
            self.callback(self.timer_id, self.status)
        
        # 타이머 스레드 생성 및 시작
        self.timer_thread = threading.Thread(target=self._run_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
        return True
    
    def pause(self) -> bool:
        """
        타이머 일시정지
        
        Returns:
            bool: 일시정지 성공 여부
        """
        if self.status != TimerStatus.RUNNING:
            return False
        
        self.status = TimerStatus.PAUSED
        self.paused_time = time.time()
        
        # 콜백 호출
        if self.callback:
            self.callback(self.timer_id, self.status)
        
        return True
    
    def resume(self) -> bool:
        """
        일시정지된 타이머 재개
        
        Returns:
            bool: 타이머 재개 성공 여부
        """
        return self.start()
    
    def cancel(self) -> bool:
        """
        타이머 취소
        
        Returns:
            bool: 타이머 취소 성공 여부
        """
        if self.status == TimerStatus.COMPLETED or self.status == TimerStatus.CANCELLED:
            return False
        
        self.status = TimerStatus.CANCELLED
        self._stop_event.set()
        
        # 콜백 호출
        if self.callback:
            self.callback(self.timer_id, self.status)
        
        return True
    
    def get_remaining_time(self) -> int:
        """
        남은 시간 계산
        
        Returns:
            int: 남은 시간(초)
        """
        if self.status == TimerStatus.READY:
            return self.duration
        elif self.status == TimerStatus.COMPLETED or self.status == TimerStatus.CANCELLED:
            return 0
        elif self.status == TimerStatus.PAUSED:
            return int(self.end_time - self.paused_time)
        else:  # RUNNING
            remaining = int(self.end_time - time.time())
            return max(0, remaining)
    
    def get_progress_percentage(self) -> float:
        """
        타이머 진행률 계산
        
        Returns:
            float: 진행률(0.0 ~ 100.0)
        """
        if self.status == TimerStatus.READY:
            return 0.0
        elif self.status == TimerStatus.COMPLETED:
            return 100.0
        elif self.status == TimerStatus.CANCELLED:
            elapsed = self.duration - self.get_remaining_time()
            return min(100.0, (elapsed / self.duration) * 100.0)
        else:  # RUNNING or PAUSED
            elapsed = self.duration - self.get_remaining_time()
            return min(100.0, (elapsed / self.duration) * 100.0)
    
    def _run_timer(self) -> None:
        """
        타이머 스레드 실행 함수
        """
        while self.status == TimerStatus.RUNNING:
            # 남은 시간 체크
            remaining = self.get_remaining_time()
            
            # 타이머 완료 처리
            if remaining <= 0:
                self.status = TimerStatus.COMPLETED
                if self.callback:
                    self.callback(self.timer_id, self.status)
                break
            
            # 중지 이벤트 확인
            if self._stop_event.wait(0.1):  # 0.1초 간격으로 체크
                break
    
    def to_dict(self) -> Dict[str, Any]:
        """
        타이머 상태를 딕셔너리로 변환
        
        Returns:
            Dict[str, Any]: 타이머 상태 정보
        """
        return {
            "timer_id": self.timer_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "duration": self.duration,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "paused_time": self.paused_time,
            "elapsed_pause_time": self.elapsed_pause_time,
            "status": self.status.value,
            "remaining_time": self.get_remaining_time(),
            "progress": self.get_progress_percentage()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], callback: Optional[Callable] = None) -> 'Timer':
        """
        딕셔너리에서 타이머 객체 생성
        
        Args:
            data (Dict[str, Any]): 타이머 상태 정보
            callback (Callable, optional): 콜백 함수
            
        Returns:
            Timer: 생성된 타이머 객체
        """
        timer = cls(
            product_id=data["product_id"],
            product_name=data["product_name"],
            duration=data["duration"],
            callback=callback
        )
        timer.timer_id = data["timer_id"]
        timer.start_time = data["start_time"]
        timer.end_time = data["end_time"]
        timer.paused_time = data["paused_time"]
        timer.elapsed_pause_time = data["elapsed_pause_time"]
        timer.status = TimerStatus(data["status"])
        
        # 필요한 경우 타이머 재시작
        if timer.status == TimerStatus.RUNNING:
            # 현재 시간이 종료 시간을 초과했는지 확인
            if time.time() > timer.end_time:
                timer.status = TimerStatus.COMPLETED
            else:
                timer._stop_event.clear()
                timer.timer_thread = threading.Thread(target=timer._run_timer)
                timer.timer_thread.daemon = True
                timer.timer_thread.start()
        
        return timer

class TimerQueue:
    """
    다중 타이머를 순차적으로 관리하는 큐 클래스
    
    속성:
        queue_id (str): 타이머 큐의 고유 ID
        name (str): 타이머 큐의 이름
        timers (List[Timer]): 타이머 목록
        current_index (int): 현재 실행 중인 타이머의 인덱스
        callback (Callable): 타이머 상태 변경 시 호출될 콜백 함수
        status (TimerStatus): 현재 타이머 큐의 상태
    """
    
    def __init__(self, name: str, callback: Optional[Callable[[str, TimerStatus, Optional[str]], None]] = None):
        """
        타이머 큐 객체 초기화
        
        Args:
            name (str): 타이머 큐의 이름
            callback (Callable, optional): 타이머 상태 변경 시 호출될 콜백 함수
        """
        self.queue_id = str(uuid.uuid4())
        self.name = name
        self.timers: List[Timer] = []
        self.current_index = -1  # 시작 전: -1
        self.callback = callback
        self.status = TimerStatus.READY
    
    def add_timer(self, timer: Timer) -> None:
        """
        타이머 큐에 타이머 추가
        
        Args:
            timer (Timer): 추가할 타이머 객체
        """
        # 타이머의 콜백을 큐의 내부 콜백으로 설정
        timer.callback = self._timer_status_changed
        self.timers.append(timer)
    
    def add_timer_from_product(self, product_id: str, product_name: str, duration: int) -> Timer:
        """
        제품 정보로 타이머를 생성하고 큐에 추가
        
        Args:
            product_id (str): 제품 ID
            product_name (str): 제품 이름
            duration (int): 타이머 지속 시간(초)
            
        Returns:
            Timer: 생성된 타이머 객체
        """
        timer = Timer(product_id, product_name, duration, callback=self._timer_status_changed)
        self.timers.append(timer)
        return timer
    
    def remove_timer(self, timer_id: str) -> bool:
        """
        타이머 큐에서 타이머 제거
        
        Args:
            timer_id (str): 제거할 타이머의 ID
            
        Returns:
            bool: 제거 성공 여부
        """
        for i, timer in enumerate(self.timers):
            if timer.timer_id == timer_id:
                # 실행 중인 타이머를 제거하는 경우 처리
                if i == self.current_index and timer.status == TimerStatus.RUNNING:
                    timer.cancel()
                    # 현재 타이머가 제거되면 다음 타이머로 이동 준비
                    if i == len(self.timers) - 1:
                        self.current_index = -1
                    
                self.timers.pop(i)
                
                # 타이머 큐가 비어있으면 상태 변경
                if not self.timers:
                    self.status = TimerStatus.COMPLETED
                    if self.callback:
                        self.callback(self.queue_id, self.status, None)
                
                return True
        
        return False
    
    def start(self) -> bool:
        """
        타이머 큐 시작 (첫 번째 타이머부터 순차 실행)
        
        Returns:
            bool: 시작 성공 여부
        """
        if not self.timers:
            return False
        
        if self.status == TimerStatus.RUNNING:
            return False
        
        # 타이머 큐가 완료 상태인 경우 초기화
        if self.status == TimerStatus.COMPLETED or self.status == TimerStatus.CANCELLED:
            for timer in self.timers:
                if timer.status != TimerStatus.READY:
                    timer.status = TimerStatus.READY
            self.current_index = -1
        
        self.status = TimerStatus.RUNNING
        
        # 콜백 호출
        if self.callback:
            self.callback(self.queue_id, self.status, None)
        
        # 다음 타이머 시작
        return self._start_next_timer()
    
    def pause(self) -> bool:
        """
        현재 실행 중인 타이머 일시정지
        
        Returns:
            bool: 일시정지 성공 여부
        """
        if self.status != TimerStatus.RUNNING or self.current_index < 0:
            return False
        
        current_timer = self.timers[self.current_index]
        if current_timer.status == TimerStatus.RUNNING:
            result = current_timer.pause()
            if result:
                self.status = TimerStatus.PAUSED
                
                # 콜백 호출
                if self.callback:
                    self.callback(self.queue_id, self.status, current_timer.timer_id)
                
            return result
        
        return False
    
    def resume(self) -> bool:
        """
        일시정지된 타이머 재개
        
        Returns:
            bool: 재개 성공 여부
        """
        if self.status != TimerStatus.PAUSED or self.current_index < 0:
            return False
        
        current_timer = self.timers[self.current_index]
        if current_timer.status == TimerStatus.PAUSED:
            result = current_timer.resume()
            if result:
                self.status = TimerStatus.RUNNING
                
                # 콜백 호출
                if self.callback:
                    self.callback(self.queue_id, self.status, current_timer.timer_id)
                
            return result
        
        return False
    
    def skip_current(self) -> bool:
        """
        현재 타이머를 건너뛰고 다음 타이머로 이동
        
        Returns:
            bool: 성공 여부
        """
        if self.current_index < 0 or self.current_index >= len(self.timers):
            return False
        
        # 현재 타이머 취소
        current_timer = self.timers[self.current_index]
        current_timer.cancel()
        
        # 다음 타이머 시작
        return self._start_next_timer()
    
    def cancel(self) -> bool:
        """
        타이머 큐 취소
        
        Returns:
            bool: 취소 성공 여부
        """
        # 현재 실행 중인 타이머 취소
        if self.current_index >= 0 and self.current_index < len(self.timers):
            current_timer = self.timers[self.current_index]
            current_timer.cancel()
        
        self.status = TimerStatus.CANCELLED
        self.current_index = -1
        
        # 콜백 호출
        if self.callback:
            self.callback(self.queue_id, self.status, None)
        
        return True
    
    def _timer_status_changed(self, timer_id: str, status: TimerStatus) -> None:
        """
        타이머 상태 변경 시 호출되는 내부 콜백 함수
        
        Args:
            timer_id (str): 상태가 변경된 타이머의 ID
            status (TimerStatus): 변경된 상태
        """
        # 타이머가 완료된 경우 다음 타이머 시작
        if status == TimerStatus.COMPLETED:
            self._start_next_timer()
        
        # 외부 콜백 호출
        if self.callback:
            self.callback(self.queue_id, self.status, timer_id)
    
    def _start_next_timer(self) -> bool:
        """
        다음 타이머 시작
        
        Returns:
            bool: 시작 성공 여부
        """
        self.current_index += 1
        
        # 모든 타이머가 완료된 경우
        if self.current_index >= len(self.timers):
            self.current_index = -1
            self.status = TimerStatus.COMPLETED
            
            # 콜백 호출
            if self.callback:
                self.callback(self.queue_id, self.status, None)
            
            return False
        
        # 다음 타이머 시작
        current_timer = self.timers[self.current_index]
        result = current_timer.start()
        
        return result
    
    def get_current_timer(self) -> Optional[Timer]:
        """
        현재 실행 중인 타이머 반환
        
        Returns:
            Optional[Timer]: 현재 타이머 또는 None
        """
        if self.current_index >= 0 and self.current_index < len(self.timers):
            return self.timers[self.current_index]
        return None
    
    def get_remaining_time(self) -> int:
        """
        현재 타이머의 남은 시간 조회
        
        Returns:
            int: 남은 시간(초) 또는 0
        """
        current_timer = self.get_current_timer()
        if current_timer:
            return current_timer.get_remaining_time()
        return 0
    
    def get_total_remaining_time(self) -> int:
        """
        모든 타이머의 총 남은 시간 조회
        
        Returns:
            int: 총 남은 시간(초)
        """
        total = 0
        for i, timer in enumerate(self.timers):
            if i >= self.current_index:
                total += timer.get_remaining_time()
        return total
    
    def get_progress_percentage(self) -> float:
        """
        전체 타이머 큐의 진행률 계산
        
        Returns:
            float: 진행률(0.0 ~ 100.0)
        """
        if not self.timers:
            return 0.0
        
        total_duration = sum(timer.duration for timer in self.timers)
        if total_duration <= 0:
            return 0.0
        
        completed_duration = 0
        
        # 완료된 타이머
        for i in range(self.current_index):
            completed_duration += self.timers[i].duration
        
        # 현재 진행 중인 타이머
        current_timer = self.get_current_timer()
        if current_timer:
            elapsed = current_timer.duration - current_timer.get_remaining_time()
            completed_duration += elapsed
        
        return min(100.0, (completed_duration / total_duration) * 100.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        타이머 큐 상태를 딕셔너리로 변환
        
        Returns:
            Dict[str, Any]: 타이머 큐 상태 정보
        """
        return {
            "queue_id": self.queue_id,
            "name": self.name,
            "current_index": self.current_index,
            "status": self.status.value,
            "timers": [timer.to_dict() for timer in self.timers],
            "total_remaining_time": self.get_total_remaining_time(),
            "progress": self.get_progress_percentage()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], callback: Optional[Callable] = None) -> 'TimerQueue':
        """
        딕셔너리에서 타이머 큐 객체 생성
        
        Args:
            data (Dict[str, Any]): 타이머 큐 상태 정보
            callback (Callable, optional): 콜백 함수
            
        Returns:
            TimerQueue: 생성된 타이머 큐 객체
        """
        queue = cls(data["name"], callback=callback)
        queue.queue_id = data["queue_id"]
        queue.current_index = data["current_index"]
        queue.status = TimerStatus(data["status"])
        
        # 타이머 복원
        for timer_data in data["timers"]:
            timer = Timer.from_dict(timer_data, callback=queue._timer_status_changed)
            queue.timers.append(timer)
        
        return queue

class StepTimer:
    """
    단계별 타이머 클래스
    
    제품의 여러 조리 단계를 순차적으로 처리하는 타이머 클래스입니다.
    
    속성:
        step_timer_id (str): 단계별 타이머의 고유 ID
        product_id (str): 제품 ID
        product_name (str): 제품 이름
        steps (List[Tuple[str, int]]): 조리 단계 목록 (설명, 시간(초))
        timer_queue (TimerQueue): 내부 타이머 큐
        callback (Callable): 단계 전환 시 호출될 콜백 함수
        current_step (int): 현재 진행 중인 단계 인덱스
    """
    
    def __init__(self, product_id: str, product_name: str, 
                 steps: List[Tuple[str, int]], 
                 callback: Optional[Callable[[str, int, str, TimerStatus], None]] = None):
        """
        단계별 타이머 초기화
        
        Args:
            product_id (str): 제품 ID
            product_name (str): 제품 이름
            steps (List[Tuple[str, int]]): 조리 단계 목록 (설명, 시간(초))
            callback (Callable, optional): 단계 전환 시 호출될 콜백 함수
        """
        self.step_timer_id = str(uuid.uuid4())
        self.product_id = product_id
        self.product_name = product_name
        self.steps = steps
        self.callback = callback
        self.current_step = -1
        
        # 내부 타이머 큐 생성
        self.timer_queue = TimerQueue(product_name, callback=self._queue_status_changed)
        
        # 단계별 타이머 생성
        for i, (step_description, step_duration) in enumerate(steps):
            timer_name = f"{product_name} - 단계 {i+1}: {step_description}"
            self.timer_queue.add_timer_from_product(
                product_id=product_id,
                product_name=timer_name,
                duration=step_duration
            )
    
    def start(self) -> bool:
        """
        단계별 타이머 시작
        
        Returns:
            bool: 시작 성공 여부
        """
        self.current_step = 0
        result = self.timer_queue.start()
        
        # 첫 번째 단계 알림
        if result and self.callback:
            step_description, _ = self.steps[0]
            self.callback(self.step_timer_id, 0, step_description, TimerStatus.RUNNING)
        
        return result
    
    def pause(self) -> bool:
        """
        단계별 타이머 일시정지
        
        Returns:
            bool: 일시정지 성공 여부
        """
        result = self.timer_queue.pause()
        
        # 일시정지 알림
        if result and self.callback and self.current_step >= 0:
            step_description, _ = self.steps[self.current_step]
            self.callback(self.step_timer_id, self.current_step, step_description, TimerStatus.PAUSED)
        
        return result
    
    def resume(self) -> bool:
        """
        단계별 타이머 재개
        
        Returns:
            bool: 재개 성공 여부
        """
        result = self.timer_queue.resume()
        
        # 재개 알림
        if result and self.callback and self.current_step >= 0:
            step_description, _ = self.steps[self.current_step]
            self.callback(self.step_timer_id, self.current_step, step_description, TimerStatus.RUNNING)
        
        return result
    
    def cancel(self) -> bool:
        """
        단계별 타이머 취소
        
        Returns:
            bool: 취소 성공 여부
        """
        result = self.timer_queue.cancel()
        
        # 취소 알림
        if result and self.callback:
            self.callback(self.step_timer_id, -1, "", TimerStatus.CANCELLED)
        
        self.current_step = -1
        return result
    
    def skip_step(self) -> bool:
        """
        현재 단계 건너뛰기
        
        Returns:
            bool: 성공 여부
        """
        if self.current_step < 0 or self.current_step >= len(self.steps):
            return False
        
        result = self.timer_queue.skip_current()
        
        # 현재 단계가 마지막이면 완료 처리
        if not result:
            self.current_step = -1
            if self.callback:
                self.callback(self.step_timer_id, -1, "", TimerStatus.COMPLETED)
        
        return True
    
    def get_current_step(self) -> Tuple[int, str, int]:
        """
        현재 단계 정보 조회
        
        Returns:
            Tuple[int, str, int]: (단계 인덱스, 단계 설명, 남은 시간)
        """
        if self.current_step < 0 or self.current_step >= len(self.steps):
            return (-1, "", 0)
        
        step_description, _ = self.steps[self.current_step]
        remaining_time = self.timer_queue.get_remaining_time()
        
        return (self.current_step, step_description, remaining_time)
    
    def get_status(self) -> TimerStatus:
        """
        현재 상태 조회
        
        Returns:
            TimerStatus: 현재 타이머 상태
        """
        return self.timer_queue.status
    
    def get_progress_percentage(self) -> float:
        """
        전체 진행률 계산
        
        Returns:
            float: 진행률(0.0 ~ 100.0)
        """
        return self.timer_queue.get_progress_percentage()
    
    def get_total_duration(self) -> int:
        """
        전체 소요 시간 조회
        
        Returns:
            int: 전체 소요 시간(초)
        """
        return sum(duration for _, duration in self.steps)
    
    def get_remaining_time(self) -> int:
        """
        남은 시간 조회
        
        Returns:
            int: 남은 시간(초)
        """
        return self.timer_queue.get_total_remaining_time()
    
    def _queue_status_changed(self, queue_id: str, status: TimerStatus, timer_id: Optional[str]) -> None:
        """
        내부 타이머 큐의 상태 변경 시 호출되는 콜백 함수
        
        Args:
            queue_id (str): 타이머 큐 ID
            status (TimerStatus): 변경된 상태
            timer_id (Optional[str]): 상태가 변경된 타이머 ID (있는 경우)
        """
        # 한 단계가 완료된 경우
        if timer_id and status == TimerStatus.RUNNING:
            # 다음 단계로 이동
            current_index = self.timer_queue.current_index
            if 0 <= current_index < len(self.steps):
                self.current_step = current_index
                step_description, _ = self.steps[current_index]
                
                # 단계 전환 알림
                if self.callback:
                    self.callback(self.step_timer_id, current_index, step_description, TimerStatus.RUNNING)
        
        # 모든 단계가 완료된 경우
        elif status == TimerStatus.COMPLETED:
            self.current_step = -1
            
            # 완료 알림
            if self.callback:
                self.callback(self.step_timer_id, -1, "", TimerStatus.COMPLETED)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        단계별 타이머 상태를 딕셔너리로 변환
        
        Returns:
            Dict[str, Any]: 단계별 타이머 상태 정보
        """
        return {
            "step_timer_id": self.step_timer_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "steps": self.steps,
            "current_step": self.current_step,
            "timer_queue": self.timer_queue.to_dict(),
            "total_duration": self.get_total_duration(),
            "remaining_time": self.get_remaining_time(),
            "progress": self.get_progress_percentage()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], callback: Optional[Callable] = None) -> 'StepTimer':
        """
        딕셔너리에서 단계별 타이머 객체 생성
        
        Args:
            data (Dict[str, Any]): 단계별 타이머 상태 정보
            callback (Callable, optional): 콜백 함수
            
        Returns:
            StepTimer: 생성된 단계별 타이머 객체
        """
        step_timer = cls(
            product_id=data["product_id"],
            product_name=data["product_name"],
            steps=data["steps"],
            callback=callback
        )
        step_timer.step_timer_id = data["step_timer_id"]
        step_timer.current_step = data["current_step"]
        
        # 내부 타이머 큐 복원
        step_timer.timer_queue = TimerQueue.from_dict(
            data["timer_queue"],
            callback=step_timer._queue_status_changed
        )
        
        return step_timer

class TimerNotification:
    """
    타이머 알림 관리 클래스
    
    타이머 완료 시 알림을 생성하고 관리하는 클래스입니다.
    """
    
    def __init__(self, sound_enabled: bool = True, use_system_notifications: bool = True):
        """
        타이머 알림 객체 초기화
        
        Args:
            sound_enabled (bool, optional): 소리 알림 활성화 여부
            use_system_notifications (bool, optional): 시스템 알림 사용 여부
        """
        self.sound_enabled = sound_enabled
        self.use_system_notifications = use_system_notifications
        self.system = platform.system()  # Windows, Darwin(macOS), Linux 등
        self.default_sound_path = self._get_default_sound_path()
        self.custom_sound_path = None
    
    def set_sound_enabled(self, enabled: bool) -> None:
        """
        소리 알림 활성화/비활성화 설정
        
        Args:
            enabled (bool): 소리 알림 활성화 여부
        """
        self.sound_enabled = enabled
    
    def set_system_notifications(self, enabled: bool) -> None:
        """
        시스템 알림 활성화/비활성화 설정
        
        Args:
            enabled (bool): 시스템 알림 활성화 여부
        """
        self.use_system_notifications = enabled
    
    def set_custom_sound(self, sound_path: Optional[str]) -> bool:
        """
        사용자 정의 알림 소리 설정
        
        Args:
            sound_path (Optional[str]): 소리 파일 경로 (None인 경우 기본 소리 사용)
            
        Returns:
            bool: 설정 성공 여부
        """
        if sound_path is None:
            self.custom_sound_path = None
            return True
        
        # 파일 존재 여부 확인
        if not os.path.exists(sound_path):
            return False
        
        self.custom_sound_path = sound_path
        return True
    
    def notify(self, title: str, message: str) -> bool:
        """
        알림 생성
        
        Args:
            title (str): 알림 제목
            message (str): 알림 메시지
            
        Returns:
            bool: 알림 생성 성공 여부
        """
        success = True
        
        # 소리 알림
        if self.sound_enabled:
            sound_success = self._play_sound()
            success = success and sound_success
        
        # 시스템 알림
        if self.use_system_notifications:
            system_success = self._show_system_notification(title, message)
            success = success and system_success
        
        # 콘솔 알림 (항상 표시)
        self._show_console_notification(title, message)
        
        return success
    
    def _play_sound(self) -> bool:
        """
        알림 소리 재생
        
        Returns:
            bool: 소리 재생 성공 여부
        """
        sound_path = self.custom_sound_path or self.default_sound_path
        
        if not sound_path:
            return False
        
        try:
            if self.system == "Windows":
                # Windows에서는 PowerShell을 사용하여 소리 재생
                command = f'powershell -c (New-Object Media.SoundPlayer "{sound_path}").PlaySync()'
                subprocess.run(command, shell=True, check=False)
            elif self.system == "Darwin":  # macOS
                command = ["afplay", sound_path]
                subprocess.run(command, check=False)
            elif self.system == "Linux":
                # Linux에서는 aplay 또는 paplay 사용
                if os.path.exists("/usr/bin/aplay"):
                    command = ["aplay", sound_path]
                    subprocess.run(command, check=False)
                elif os.path.exists("/usr/bin/paplay"):
                    command = ["paplay", sound_path]
                    subprocess.run(command, check=False)
                else:
                    return False
            else:
                return False
            
            return True
        except Exception:
            return False
    
    def _show_system_notification(self, title: str, message: str) -> bool:
        """
        시스템 알림 표시
        
        Args:
            title (str): 알림 제목
            message (str): 알림 메시지
            
        Returns:
            bool: 알림 표시 성공 여부
        """
        try:
            if self.system == "Windows":
                # Windows에서는 PowerShell을 사용하여 알림 표시
                script = f'''
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

                $APP_ID = "K-Food-Timer"
                $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
                $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
                $text = $xml.GetElementsByTagName("text")
                $text[0].AppendChild($xml.CreateTextNode("{title}"))
                $text[1].AppendChild($xml.CreateTextNode("{message}"))
                $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show($toast)
                '''
                subprocess.run(["powershell", "-Command", script], check=False)
            elif self.system == "Darwin":  # macOS
                # macOS에서는 osascript 사용
                script = f'display notification "{message}" with title "{title}"'
                subprocess.run(["osascript", "-e", script], check=False)
            elif self.system == "Linux":
                # Linux에서는 notify-send 사용
                subprocess.run(["notify-send", title, message], check=False)
            else:
                return False
            
            return True
        except Exception:
            return False
    
    def _show_console_notification(self, title: str, message: str) -> None:
        """
        콘솔에 알림 표시
        
        Args:
            title (str): 알림 제목
            message (str): 알림 메시지
        """
        print("\n" + "=" * 50)
        print(f"[{title}]")
        print(message)
        print("=" * 50)
    
    def _get_default_sound_path(self) -> Optional[str]:
        """
        기본 알림 소리 파일 경로 조회
        
        Returns:
            Optional[str]: 소리 파일 경로 또는 None
        """
        if self.system == "Windows":
            return os.path.join(os.environ.get("SYSTEMROOT", "C:\\Windows"), "Media", "Alarm01.wav")
        elif self.system == "Darwin":  # macOS
            return "/System/Library/Sounds/Ping.aiff"
        elif self.system == "Linux":
            # 일반적인 Linux 소리 파일 위치
            sound_paths = [
                "/usr/share/sounds/freedesktop/stereo/complete.oga",
                "/usr/share/sounds/gnome/default/alerts/glass.ogg",
                "/usr/share/sounds/ubuntu/stereo/bell.ogg"
            ]
            for path in sound_paths:
                if os.path.exists(path):
                    return path
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        알림 설정을 딕셔너리로 변환
        
        Returns:
            Dict[str, Any]: 알림 설정 정보
        """
        return {
            "sound_enabled": self.sound_enabled,
            "use_system_notifications": self.use_system_notifications,
            "custom_sound_path": self.custom_sound_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimerNotification':
        """
        딕셔너리에서 알림 객체 생성
        
        Args:
            data (Dict[str, Any]): 알림 설정 정보
            
        Returns:
            TimerNotification: 생성된 알림 객체
        """
        notification = cls(
            sound_enabled=data.get("sound_enabled", True),
            use_system_notifications=data.get("use_system_notifications", True)
        )
        
        custom_sound_path = data.get("custom_sound_path")
        if custom_sound_path:
            notification.set_custom_sound(custom_sound_path)
        
        return notification

class TimerStorage:
    """
    타이머 상태 저장 및 불러오기 클래스
    
    타이머, 타이머 큐 및 단계별 타이머의 상태를 JSON 형식으로 저장하고 불러오는 기능을 제공합니다.
    """
    
    def __init__(self, storage_dir: str = "data"):
        """
        타이머 저장소 초기화
        
        Args:
            storage_dir (str, optional): 저장 디렉토리 경로
        """
        self.storage_dir = storage_dir
        self.timers_file = os.path.join(storage_dir, "timers.json")
        
        # 저장 디렉토리 생성
        os.makedirs(storage_dir, exist_ok=True)
    
    def save_timer(self, timer: Timer) -> bool:
        """
        타이머 상태 저장
        
        Args:
            timer (Timer): 저장할 타이머 객체
            
        Returns:
            bool: 저장 성공 여부
        """
        return self._save_object("timer", timer.timer_id, timer.to_dict())
    
    def save_timer_queue(self, queue: TimerQueue) -> bool:
        """
        타이머 큐 상태 저장
        
        Args:
            queue (TimerQueue): 저장할 타이머 큐 객체
            
        Returns:
            bool: 저장 성공 여부
        """
        return self._save_object("queue", queue.queue_id, queue.to_dict())
    
    def save_step_timer(self, step_timer: StepTimer) -> bool:
        """
        단계별 타이머 상태 저장
        
        Args:
            step_timer (StepTimer): 저장할 단계별 타이머 객체
            
        Returns:
            bool: 저장 성공 여부
        """
        return self._save_object("step_timer", step_timer.step_timer_id, step_timer.to_dict())
    
    def load_timer(self, timer_id: str, callback: Optional[Callable] = None) -> Optional[Timer]:
        """
        타이머 상태 불러오기
        
        Args:
            timer_id (str): 불러올 타이머 ID
            callback (Callable, optional): 콜백 함수
            
        Returns:
            Optional[Timer]: 불러온 타이머 객체 또는 None
        """
        data = self._load_object("timer", timer_id)
        if not data:
            return None
        
        return Timer.from_dict(data, callback=callback)
    
    def load_timer_queue(self, queue_id: str, callback: Optional[Callable] = None) -> Optional[TimerQueue]:
        """
        타이머 큐 상태 불러오기
        
        Args:
            queue_id (str): 불러올 타이머 큐 ID
            callback (Callable, optional): 콜백 함수
            
        Returns:
            Optional[TimerQueue]: 불러온 타이머 큐 객체 또는 None
        """
        data = self._load_object("queue", queue_id)
        if not data:
            return None
        
        return TimerQueue.from_dict(data, callback=callback)
    
    def load_step_timer(self, step_timer_id: str, callback: Optional[Callable] = None) -> Optional[StepTimer]:
        """
        단계별 타이머 상태 불러오기
        
        Args:
            step_timer_id (str): 불러올 단계별 타이머 ID
            callback (Callable, optional): 콜백 함수
            
        Returns:
            Optional[StepTimer]: 불러온 단계별 타이머 객체 또는 None
        """
        data = self._load_object("step_timer", step_timer_id)
        if not data:
            return None
        
        return StepTimer.from_dict(data, callback=callback)
    
    def load_all_timers(self, callback: Optional[Callable] = None) -> Dict[str, Timer]:
        """
        모든 타이머 상태 불러오기
        
        Args:
            callback (Callable, optional): 콜백 함수
            
        Returns:
            Dict[str, Timer]: 타이머 ID를 키로 하는 타이머 딕셔너리
        """
        return self._load_all_objects("timer", lambda data: Timer.from_dict(data, callback=callback))
    
    def load_all_timer_queues(self, callback: Optional[Callable] = None) -> Dict[str, TimerQueue]:
        """
        모든 타이머 큐 상태 불러오기
        
        Args:
            callback (Callable, optional): 콜백 함수
            
        Returns:
            Dict[str, TimerQueue]: 타이머 큐 ID를 키로 하는 타이머 큐 딕셔너리
        """
        return self._load_all_objects("queue", lambda data: TimerQueue.from_dict(data, callback=callback))
    
    def load_all_step_timers(self, callback: Optional[Callable] = None) -> Dict[str, StepTimer]:
        """
        모든 단계별 타이머 상태 불러오기
        
        Args:
            callback (Callable, optional): 콜백 함수
            
        Returns:
            Dict[str, StepTimer]: 단계별 타이머 ID를 키로 하는 단계별 타이머 딕셔너리
        """
        return self._load_all_objects("step_timer", lambda data: StepTimer.from_dict(data, callback=callback))
    
    def delete_timer(self, timer_id: str) -> bool:
        """
        타이머 상태 삭제
        
        Args:
            timer_id (str): 삭제할 타이머 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        return self._delete_object("timer", timer_id)
    
    def delete_timer_queue(self, queue_id: str) -> bool:
        """
        타이머 큐 상태 삭제
        
        Args:
            queue_id (str): 삭제할 타이머 큐 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        return self._delete_object("queue", queue_id)
    
    def delete_step_timer(self, step_timer_id: str) -> bool:
        """
        단계별 타이머 상태 삭제
        
        Args:
            step_timer_id (str): 삭제할 단계별 타이머 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        return self._delete_object("step_timer", step_timer_id)
    
    def _save_object(self, obj_type: str, obj_id: str, data: Dict[str, Any]) -> bool:
        """
        객체 저장
        
        Args:
            obj_type (str): 객체 유형
            obj_id (str): 객체 ID
            data (Dict[str, Any]): 저장할 데이터
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            timers_data = self._load_timers_data()
            
            # 객체 유형에 대한 딕셔너리가 없으면 생성
            if obj_type not in timers_data:
                timers_data[obj_type] = {}
            
            # 객체 데이터 저장
            timers_data[obj_type][obj_id] = data
            
            # 파일에 저장
            with open(self.timers_file, "w", encoding="utf-8") as f:
                json.dump(timers_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception:
            return False
    
    def _load_object(self, obj_type: str, obj_id: str) -> Optional[Dict[str, Any]]:
        """
        객체 불러오기
        
        Args:
            obj_type (str): 객체 유형
            obj_id (str): 객체 ID
            
        Returns:
            Optional[Dict[str, Any]]: 불러온 데이터 또는 None
        """
        timers_data = self._load_timers_data()
        
        if obj_type not in timers_data or obj_id not in timers_data[obj_type]:
            return None
        
        return timers_data[obj_type][obj_id]
    
    def _delete_object(self, obj_type: str, obj_id: str) -> bool:
        """
        객체 삭제
        
        Args:
            obj_type (str): 객체 유형
            obj_id (str): 객체 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            timers_data = self._load_timers_data()
            
            if obj_type not in timers_data or obj_id not in timers_data[obj_type]:
                return False
            
            # 객체 삭제
            del timers_data[obj_type][obj_id]
            
            # 파일에 저장
            with open(self.timers_file, "w", encoding="utf-8") as f:
                json.dump(timers_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception:
            return False
    
    def _load_all_objects(self, obj_type: str, factory_func: Callable[[Dict[str, Any]], Any]) -> Dict[str, Any]:
        """
        특정 유형의 모든 객체 불러오기
        
        Args:
            obj_type (str): 객체 유형
            factory_func (Callable): 객체 생성 함수
            
        Returns:
            Dict[str, Any]: ID를 키로 하는 객체 딕셔너리
        """
        timers_data = self._load_timers_data()
        
        if obj_type not in timers_data:
            return {}
        
        result = {}
        
        for obj_id, data in timers_data[obj_type].items():
            try:
                obj = factory_func(data)
                if obj:
                    result[obj_id] = obj
            except Exception:
                # 객체 생성 실패 시 무시
                pass
        
        return result
    
    def _load_timers_data(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        타이머 데이터 파일 불러오기
        
        Returns:
            Dict: 타이머 데이터
        """
        if not os.path.exists(self.timers_file):
            return {"timer": {}, "queue": {}, "step_timer": {}}
        
        try:
            with open(self.timers_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"timer": {}, "queue": {}, "step_timer": {}}

# 사용 예제
def usage_example():
    """
    타이머 모듈 사용 예제
    """
    # 1. 기본 타이머 사용 예제
    def timer_callback(timer_id, status):
        print(f"타이머 상태 변경: {timer_id} - {status}")
        if status == TimerStatus.COMPLETED:
            print("타이머가 완료되었습니다!")
    
    # 타이머 생성
    timer = Timer(
        product_id="ramyun_1",
        product_name="신라면",
        duration=180,  # 3분
        callback=timer_callback
    )
    
    # 타이머 시작
    timer.start()
    
    # 타이머 일시정지 (1초 후)
    time.sleep(1)
    timer.pause()
    
    # 타이머 재개 (1초 후)
    time.sleep(1)
    timer.resume()
    
    # 타이머 상태 및 남은 시간 확인
    print(f"타이머 상태: {timer.status}")
    print(f"남은 시간: {timer.get_remaining_time()}초")
    print(f"진행률: {timer.get_progress_percentage()}%")
    
    # 2. 타이머 큐 사용 예제
    def queue_callback(queue_id, status, timer_id):
        print(f"타이머 큐 상태 변경: {queue_id} - {status} (타이머: {timer_id})")
    
    # 타이머 큐 생성
    queue = TimerQueue("조리 과정", callback=queue_callback)
    
    # 타이머 추가
    queue.add_timer_from_product("step_1", "물 끓이기", 60)
    queue.add_timer_from_product("step_2", "면 넣기", 180)
    queue.add_timer_from_product("step_3", "스프 넣기", 30)
    
    # 타이머 큐 시작
    queue.start()
    
    # 현재 타이머 정보 및 진행률 확인
    current_timer = queue.get_current_timer()
    if current_timer:
        print(f"현재 단계: {current_timer.product_name}")
        print(f"남은 시간: {current_timer.get_remaining_time()}초")
    
    print(f"총 남은 시간: {queue.get_total_remaining_time()}초")
    print(f"전체 진행률: {queue.get_progress_percentage()}%")
    
    # 3. 단계별 타이머 사용 예제
    def step_timer_callback(step_timer_id, step_index, step_description, status):
        print(f"단계 변경: {step_timer_id} - 단계 {step_index}: {step_description} ({status})")
    
    # 단계별 타이머 생성
    steps = [
        ("물 끓이기", 60),
        ("면 넣기", 180),
        ("스프 넣기", 30)
    ]
    
    step_timer = StepTimer(
        product_id="ramyun_1",
        product_name="신라면",
        steps=steps,
        callback=step_timer_callback
    )
    
    # 단계별 타이머 시작
    step_timer.start()
    
    # 현재 단계 정보 확인
    step_index, step_description, remaining_time = step_timer.get_current_step()
    print(f"현재 단계: {step_index + 1}. {step_description} (남은 시간: {remaining_time}초)")
    
    # 4. 타이머 알림 사용 예제
    notification = TimerNotification()
    notification.notify("타이머 완료", "라면 조리가 완료되었습니다!")
    
    # 5. 타이머 상태 저장 및 불러오기 예제
    storage = TimerStorage()
    
    # 타이머 저장
    storage.save_timer(timer)
    
    # 타이머 불러오기
    loaded_timer = storage.load_timer(timer.timer_id, callback=timer_callback)
    if loaded_timer:
        print(f"불러온 타이머: {loaded_timer.product_name} (남은 시간: {loaded_timer.get_remaining_time()}초)")

# 모듈이 직접 실행되는 경우 예제 실행
if __name__ == "__main__":
    usage_example() 