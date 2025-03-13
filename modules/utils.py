#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K-Food Timer 애플리케이션의 공통 유틸리티 기능

이 모듈은 여러 모듈에서 공통으로 사용되는 유틸리티 함수들을 포함합니다.
"""

import os
import platform
import datetime
from functools import lru_cache

# 시간 포맷팅 함수
@lru_cache(maxsize=128)
def format_time(seconds):
    """시간(초)을 읽기 쉬운 형식으로 변환
    
    Args:
        seconds (int): 초 단위 시간
        
    Returns:
        str: 형식화된 시간 문자열 (MM:SS 또는 HH:MM:SS)
    """
    if seconds < 3600:  # 1시간 미만
        minutes, secs = divmod(seconds, 60)
        return f"{minutes:02}:{secs:02}"
    else:  # 1시간 이상
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{secs:02}"

# 운영체제별 호환성 처리를 위한 소리 재생 함수 정의
def play_sound(sound_file=None):
    """소리 재생 (운영체제별 처리)
    
    Args:
        sound_file (str, optional): 소리 파일 경로 (기본값: None)
    """
    try:
        if platform.system() == "Windows":
            import winsound
            winsound.Beep(1000, 500)  # 주파수 1000Hz, 0.5초 동안
        elif platform.system() == "Darwin":  # macOS
            os.system("afplay /System/Library/Sounds/Tink.aiff")
        else:  # Linux 등
            os.system("echo -e '\a'")  # 터미널 비프음
            
    except Exception as e:
        print(f"소리 재생 중 오류 발생: {e}")

# 화면 지우기 함수
def clear_screen():
    """현재 터미널 화면 지우기 (운영체제별 처리)"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

# 날짜/시간 관련 유틸리티
def get_current_datetime():
    """현재 날짜와 시간 반환
    
    Returns:
        datetime: 현재 datetime 객체
    """
    return datetime.datetime.now()

def format_datetime(dt):
    """datetime 객체를 사용자 친화적인 형식으로 변환
    
    Args:
        dt (datetime): 변환할 datetime 객체
        
    Returns:
        str: 형식화된 날짜/시간 문자열
    """
    if not dt:
        return "없음"
    return dt.strftime("%Y년 %m월 %d일 %H:%M") 