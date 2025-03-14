#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K-Food 타이머 모듈 데모 스크립트

이 스크립트는 타이머 모듈의 주요 기능을 시연합니다.
- 기본 타이머 기능
- 다중 타이머 관리
- 단계별 타이머
- 알림 시스템
- 타이머 상태 저장 및 불러오기
"""

import os
import time
import threading
import sys
from pathlib import Path

# 현재 디렉토리를 모듈 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.timer_module import (
    Timer, TimerQueue, StepTimer, TimerStatus, 
    TimerNotification, TimerStorage
)

def clear_screen():
    """화면 지우기"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """데모 섹션 헤더 출력"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def wait_key(message="계속하려면 아무 키나 누르세요..."):
    """키 입력 대기"""
    print(f"\n{message}")
    if os.name == 'nt':  # Windows
        import msvcrt
        msvcrt.getch()
    else:  # Unix/Linux/Mac
        import termios, tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def demo_basic_timer():
    """기본 타이머 데모"""
    print_header("1. 기본 타이머 데모")
    
    print("5초 타이머를 생성하고 시작합니다.")
    
    # 타이머 상태 변경 콜백 함수
    def on_timer_status_changed(timer_id, status):
        if status == TimerStatus.COMPLETED:
            print(f"\n타이머가 완료되었습니다!")
        elif status == TimerStatus.PAUSED:
            print(f"\n타이머가 일시정지되었습니다.")
        elif status == TimerStatus.RUNNING:
            print(f"\n타이머가 실행 중입니다.")
    
    # 타이머 생성 및 시작
    timer = Timer(
        product_id="demo_product_1",
        product_name="데모 제품",
        duration=5,  # 5초
        callback=on_timer_status_changed
    )
    
    timer.start()
    
    # 타이머 진행 상황 표시
    stop_thread = threading.Event()
    
    def show_progress():
        while not stop_thread.is_set():
            if timer.status == TimerStatus.COMPLETED:
                break
                
            remaining = timer.get_remaining_time()
            progress = timer.get_progress_percentage()
            
            # 프로그레스 바 생성
            bar_length = 40
            filled_length = int(bar_length * progress / 100)
            bar = '=' * filled_length + ' ' * (bar_length - filled_length)
            
            # 진행 상황 출력
            sys.stdout.write(f"\r진행 상황: [{bar}] {progress:.1f}% (남은 시간: {remaining}초) ")
            sys.stdout.flush()
            
            time.sleep(0.1)
    
    # 진행 상황 표시 스레드 시작
    progress_thread = threading.Thread(target=show_progress)
    progress_thread.daemon = True
    progress_thread.start()
    
    # 2초 후 타이머 일시정지
    time.sleep(2)
    timer.pause()
    
    wait_key("타이머를 재개하려면 아무 키나 누르세요...")
    
    # 타이머 재개
    timer.resume()
    
    # 타이머 완료 대기
    while timer.status != TimerStatus.COMPLETED:
        time.sleep(0.1)
    
    # 진행 상황 표시 스레드 종료
    stop_thread.set()
    progress_thread.join()
    
    print("\n\n기본 타이머 데모가 완료되었습니다.")
    wait_key()

def demo_timer_queue():
    """타이머 큐 데모"""
    print_header("2. 다중 타이머 큐 데모")
    
    print("3개의 타이머가 포함된 큐를 생성하고 시작합니다.")
    
    # 타이머 큐 상태 변경 콜백 함수
    def on_queue_status_changed(queue_id, status, timer_id):
        if status == TimerStatus.COMPLETED:
            print(f"\n모든 타이머가 완료되었습니다!")
        elif timer_id:
            current_timer = queue.get_current_timer()
            if current_timer:
                print(f"\n현재 타이머: {current_timer.product_name}")
    
    # 타이머 큐 생성
    queue = TimerQueue("데모 큐", callback=on_queue_status_changed)
    
    # 타이머 추가
    queue.add_timer_from_product("step_1", "첫 번째 타이머 (3초)", 3)
    queue.add_timer_from_product("step_2", "두 번째 타이머 (2초)", 2)
    queue.add_timer_from_product("step_3", "세 번째 타이머 (1초)", 1)
    
    # 타이머 큐 시작
    queue.start()
    
    # 타이머 큐 진행 상황 표시
    stop_thread = threading.Event()
    
    def show_queue_progress():
        while not stop_thread.is_set():
            if queue.status == TimerStatus.COMPLETED:
                break
                
            total_remaining = queue.get_total_remaining_time()
            progress = queue.get_progress_percentage()
            current_timer = queue.get_current_timer()
            
            if current_timer:
                current_remaining = current_timer.get_remaining_time()
                current_progress = current_timer.get_progress_percentage()
                
                # 현재 타이머 프로그레스 바 생성
                bar_length = 30
                filled_length = int(bar_length * current_progress / 100)
                current_bar = '=' * filled_length + ' ' * (bar_length - filled_length)
                
                # 전체 프로그레스 바 생성
                filled_length = int(bar_length * progress / 100)
                total_bar = '=' * filled_length + ' ' * (bar_length - filled_length)
                
                # 진행 상황 출력
                sys.stdout.write(f"\r현재: [{current_bar}] {current_progress:.1f}% ({current_remaining}초) | "
                                f"전체: [{total_bar}] {progress:.1f}% ({total_remaining}초)")
                sys.stdout.flush()
            
            time.sleep(0.1)
    
    # 진행 상황 표시 스레드 시작
    progress_thread = threading.Thread(target=show_queue_progress)
    progress_thread.daemon = True
    progress_thread.start()
    
    # 타이머 큐 완료 대기
    while queue.status != TimerStatus.COMPLETED:
        time.sleep(0.1)
    
    # 진행 상황 표시 스레드 종료
    stop_thread.set()
    progress_thread.join()
    
    print("\n\n다중 타이머 큐 데모가 완료되었습니다.")
    wait_key()

def demo_step_timer():
    """단계별 타이머 데모"""
    print_header("3. 단계별 타이머 데모")
    
    print("라면 조리를 위한 3단계 타이머를 생성하고 시작합니다.")
    
    # 조리 단계 정의
    steps = [
        ("물 끓이기", 3),  # 3초
        ("면과 스프 넣기", 2),  # 2초
        ("뚜껑 덮고 기다리기", 1)  # 1초
    ]
    
    # 단계 변경 콜백 함수
    def on_step_changed(step_timer_id, step_index, step_description, status):
        if status == TimerStatus.COMPLETED:
            print(f"\n모든 단계가 완료되었습니다!")
        elif status == TimerStatus.RUNNING:
            print(f"\n현재 단계: {step_index + 1}. {step_description}")
    
    # 단계별 타이머 생성
    step_timer = StepTimer(
        product_id="ramyun_1",
        product_name="신라면",
        steps=steps,
        callback=on_step_changed
    )
    
    # 단계별 타이머 시작
    step_timer.start()
    
    # 단계별 타이머 진행 상황 표시
    stop_thread = threading.Event()
    
    def show_step_progress():
        while not stop_thread.is_set():
            if step_timer.get_status() == TimerStatus.COMPLETED:
                break
                
            step_index, step_description, remaining = step_timer.get_current_step()
            total_remaining = step_timer.get_remaining_time()
            progress = step_timer.get_progress_percentage()
            
            if step_index >= 0:
                # 프로그레스 바 생성
                bar_length = 40
                filled_length = int(bar_length * progress / 100)
                bar = '=' * filled_length + ' ' * (bar_length - filled_length)
                
                # 진행 상황 출력
                sys.stdout.write(f"\r진행 상황: [{bar}] {progress:.1f}% | "
                                f"단계 {step_index + 1}/{len(steps)}: {remaining}초 | "
                                f"총 남은 시간: {total_remaining}초")
                sys.stdout.flush()
            
            time.sleep(0.1)
    
    # 진행 상황 표시 스레드 시작
    progress_thread = threading.Thread(target=show_step_progress)
    progress_thread.daemon = True
    progress_thread.start()
    
    # 단계별 타이머 완료 대기
    while step_timer.get_status() != TimerStatus.COMPLETED:
        time.sleep(0.1)
    
    # 진행 상황 표시 스레드 종료
    stop_thread.set()
    progress_thread.join()
    
    print("\n\n단계별 타이머 데모가 완료되었습니다.")
    wait_key()

def demo_notification():
    """알림 시스템 데모"""
    print_header("4. 알림 시스템 데모")
    
    notification = TimerNotification()
    
    print("알림 테스트를 시작합니다. 화면과 소리로 알림이 표시됩니다.")
    print("알림이 보이지 않거나 소리가 들리지 않는 경우, 시스템 설정을 확인하세요.")
    
    wait_key("알림을 보내려면 아무 키나 누르세요...")
    
    # 알림 전송
    notification.notify(
        "타이머 완료", 
        "K-Food 타이머 - 라면 조리가 완료되었습니다!"
    )
    
    print("\n알림 시스템 데모가 완료되었습니다.")
    wait_key()

def demo_timer_storage():
    """타이머 상태 저장 및 불러오기 데모"""
    print_header("5. 타이머 상태 저장 및 불러오기 데모")
    
    # 저장 디렉토리 생성
    data_dir = Path("demo_data")
    data_dir.mkdir(exist_ok=True)
    
    # 타이머 저장소 생성
    storage = TimerStorage(storage_dir=str(data_dir))
    
    # 저장할 타이머 생성
    timer = Timer(
        product_id="save_test",
        product_name="저장 테스트 제품",
        duration=30
    )
    
    # 타이머 시작
    timer.start()
    
    # 1초 후 일시정지
    time.sleep(1)
    timer.pause()
    
    print(f"타이머 생성 및 1초 실행 후 일시정지: {timer.timer_id}")
    
    # 타이머 상태 저장
    storage.save_timer(timer)
    print(f"타이머 상태가 '{data_dir}/timers.json'에 저장되었습니다.")
    
    # 타이머 ID 저장
    saved_timer_id = timer.timer_id
    
    # 타이머 변수 제거 (메모리에서 삭제)
    del timer
    
    wait_key("저장된 타이머를 불러오려면 아무 키나 누르세요...")
    
    # 저장된 타이머 불러오기
    loaded_timer = storage.load_timer(saved_timer_id)
    
    if loaded_timer:
        print(f"타이머를 성공적으로 불러왔습니다: {loaded_timer.timer_id}")
        print(f"제품명: {loaded_timer.product_name}")
        print(f"상태: {loaded_timer.status.value}")
        print(f"남은 시간: {loaded_timer.get_remaining_time()}초")
        
        # 불러온 타이머 재개
        wait_key("불러온 타이머를 재개하려면 아무 키나 누르세요...")
        loaded_timer.resume()
        
        # 진행 상황 표시
        for _ in range(3):
            remaining = loaded_timer.get_remaining_time()
            progress = loaded_timer.get_progress_percentage()
            print(f"남은 시간: {remaining}초, 진행률: {progress:.1f}%")
            time.sleep(1)
        
        # 타이머 취소
        loaded_timer.cancel()
    else:
        print("타이머를 불러오지 못했습니다.")
    
    print("\n타이머 상태 저장 및 불러오기 데모가 완료되었습니다.")
    wait_key()

def main():
    """메인 데모 함수"""
    try:
        clear_screen()
        print_header("K-Food 타이머 모듈 데모")
        print("이 데모는 K-Food 타이머 모듈의 주요 기능을 시연합니다.")
        print("각 데모를 차례대로 실행합니다.")
        wait_key()
        
        demo_basic_timer()
        clear_screen()
        
        demo_timer_queue()
        clear_screen()
        
        demo_step_timer()
        clear_screen()
        
        demo_notification()
        clear_screen()
        
        demo_timer_storage()
        clear_screen()
        
        print_header("데모 완료")
        print("K-Food 타이머 모듈 데모가 모두 완료되었습니다.")
        print("이 데모에서는 다음 기능을 시연했습니다:")
        print("- 기본 타이머 기능 (시작, 일시정지, 재개)")
        print("- 다중 타이머 관리 (타이머 큐)")
        print("- 단계별 타이머 (조리 단계별 순차 실행)")
        print("- 알림 시스템 (소리 및 화면 알림)")
        print("- 타이머 상태 저장 및 불러오기")
        print("\n타이머 모듈을 자유롭게 활용해보세요!")
        
    except KeyboardInterrupt:
        print("\n\n데모가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n데모 실행 중 오류가 발생했습니다: {e}")
    
    print("\n데모를 종료합니다. 감사합니다!")

if __name__ == "__main__":
    main() 