#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
사용자 인터페이스를 관리하는 모듈

이 모듈은 K-Food Timer 애플리케이션의 콘솔 기반 UI를 구현합니다.
메뉴 시스템, 사용자 입력 처리, 타이머 관리 인터페이스 등을 제공합니다.
"""

import os
import sys
import time
import threading
import platform
from datetime import datetime
from functools import lru_cache  # 캐싱을 위한 데코레이터 추가
from itertools import islice  # 제네레이터 처리용
import msvcrt
import logging
from typing import List, Dict, Any, Optional, Callable

# 분리된 모듈 import
from modules.utils import clear_screen, format_time, format_datetime, get_current_datetime
from modules.menu_module import MenuManager
from modules.notification_module import NotificationManager
from .product_module import Product

logger = logging.getLogger(__name__)

# 운영체제별 호환성 처리를 위한 소리 재생 함수 정의
if platform.system() == "Windows":
    import winsound
    
    def play_sound(sound_file=None):
        """소리 재생 - Windows 환경
        
        Args:
            sound_file (str, optional): 소리 파일 경로 (기본값: None)
        """
        try:
            winsound.Beep(1000, 500)  # 주파수 1000Hz, 0.5초 동안
        except Exception as e:
            print(f"소리 재생 중 오류 발생: {e}")
            
elif platform.system() == "Darwin":  # macOS
    def play_sound(sound_file=None):
        """소리 재생 - macOS 환경
        
        Args:
            sound_file (str, optional): 소리 파일 경로 (기본값: None)
        """
        try:
            os.system("afplay /System/Library/Sounds/Tink.aiff")
        except Exception as e:
            print(f"소리 재생 중 오류 발생: {e}")
            
else:  # Linux 등
    def play_sound(sound_file=None):
        """소리 재생 - Linux 및 기타 환경
        
        Args:
            sound_file (str, optional): 소리 파일 경로 (기본값: None)
        """
        try:
            os.system("aplay -q /usr/share/sounds/sound-icons/glass-water-1.wav 2>/dev/null || echo -e '\a'")
        except Exception as e:
            print(f"소리 재생 중 오류 발생: {e}")
            print("\a")  # 콘솔 비프음

# 운영 체제 타입 한 번만 확인 (반복 호출 방지)
CURRENT_OS = platform.system()

# 화면 지우기 명령 미리 정의
CLEAR_COMMAND = "cls" if CURRENT_OS == "Windows" else "clear"

# 상수 정의
BACK_TO_MAIN_MSG = "엔터 키를 눌러 메인 메뉴로 돌아가세요..."
MENU_BACK_TO_CATEGORY_MSG = "엔터 키를 눌러 카테고리 메뉴로 돌아가세요..."

class UI:
    """사용자 인터페이스 클래스
    
    K-Food 타이머 앱의 모든 UI 기능을 담당합니다.
    """
    
    def __init__(self, app):
        """UI 초기화
        
        Args:
            app: 앱 메인 객체 (KFoodTimer 인스턴스)
        """
        self.app = app
        self.width = 60  # UI 너비
        # 컨텍스트 관리를 위한 변수 추가
        self.navigation_stack = []  # 내비게이션 스택
        self.current_context = {}  # 현재 컨텍스트 정보
        
    def push_context(self, menu_name, context_data=None):
        """컨텍스트를 스택에 추가
        
        Args:
            menu_name (str): 현재 메뉴 이름
            context_data (dict, optional): 컨텍스트 데이터
        """
        context = {
            'menu': menu_name,
            'data': context_data or {},
            'timestamp': datetime.now()
        }
        self.navigation_stack.append(context)
        self.current_context = context
        
    def pop_context(self):
        """이전 컨텍스트로 복원
        
        Returns:
            dict: 이전 컨텍스트 데이터 또는 None
        """
        if len(self.navigation_stack) > 1:
            self.navigation_stack.pop()  # 현재 컨텍스트 제거
            self.current_context = self.navigation_stack[-1]  # 이전 컨텍스트로 설정
            return self.current_context
        return None
        
    def display_breadcrumb(self):
        """현재 메뉴 경로 표시"""
        if self.navigation_stack:
            breadcrumb = " > ".join([ctx['menu'] for ctx in self.navigation_stack])
            print(f"\n경로: {breadcrumb}\n")
        
    def clear_screen(self) -> None:
        """화면 지우기"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def display_header(self) -> None:
        """헤더 표시"""
        self.clear_screen()
        print("=" * self.width)
        print(f"{'K-FOOD TIMER':^{self.width}}")
        print("=" * self.width)
        
        # 브레드크럼과 컨텍스트 정보 표시
        if self.navigation_stack:
            self.display_breadcrumb()
            
        # 현재 작업 중인 컨텍스트가 있으면 표시
        if self.current_context and 'data' in self.current_context and self.current_context['data']:
            context_data = self.current_context['data']
            if 'product' in context_data:
                product = context_data['product']
                print(f"현재 작업 중: {product.get_localized_name()}")
            if 'category' in context_data:
                category = context_data['category']
                print(f"현재 카테고리: {category}")
            print("-" * self.width)
    
    def display_menu_header(self, title):
        """메뉴 헤더 표시
        
        Args:
            title (str): 메뉴 제목
        """
        self.display_header()
        print(f"{title:^{self.width}}")
        print("-" * self.width + "\n")
        
    def main_menu(self) -> None:
        """메인 메뉴 표시"""
        # 새로운 탐색 시작 - 스택 초기화
        self.navigation_stack = []
        self.push_context("메인 메뉴")
        
        self.display_menu_header("메인 메뉴")
        
        menu_items = [
            "1. 카테고리별 제품 선택",
            "2. 즐겨찾기 제품",
            "3. 최근 사용 제품",
            "4. 제품 검색",
            "5. 설정",
            "0. 종료"
        ]
        
        for item in menu_items:
            print(item)
            
        print("\n선택: ", end="")
        choice = input().strip()
        
        if choice == "1":
            self.category_menu()
        elif choice == "2":
            self.favorite_products_menu()
        elif choice == "3":
            self.recent_products_menu()
        elif choice == "4":
            self.search_products()
        elif choice == "5":
            self.settings_menu()
        elif choice == "0":
            self.exit_app()
        else:
            print("\n잘못된 선택입니다. 다시 시도하세요.")
            time.sleep(1.5)
            self.main_menu()
            
    def category_menu(self) -> None:
        """카테고리 메뉴 표시"""
        self.push_context("카테고리 선택")
        self.display_menu_header("카테고리 선택")
        
        categories = self.app.get_categories()
        
        for i, category in enumerate(categories, 1):
            print(f"{i}. {category}")
            
        print("\n0. 이전 메뉴")
        print("\n선택: ", end="")
        choice = input().strip()
        
        if choice == "0":
            self.pop_context()  # 컨텍스트 제거
            self.main_menu()
            return
            
        try:
            index = int(choice) - 1
            if 0 <= index < len(categories):
                self.product_list_menu(categories[index])
            else:
                print("\n잘못된 선택입니다.")
                time.sleep(1.5)
                self.category_menu()
        except ValueError:
            print("\n숫자를 입력하세요.")
            time.sleep(1.5)
            self.category_menu()
            
    def product_list_menu(self, category: str) -> None:
        """카테고리별 제품 목록 메뉴 표시
        
        Args:
            category (str): 표시할 카테고리
        """
        self.push_context("제품 목록", {'category': category})
        self.display_menu_header(f"{category} 제품 목록")
        
        products = self.app.get_products_by_category(category)
        if not products:
            print("이 카테고리에 제품이 없습니다.")
            print("\n0. 이전 메뉴")
            choice = input("\n선택: ").strip()
            if choice == "0":
                self.pop_context()
                self.category_menu()
            return
            
        for i, product in enumerate(products, 1):
            name = product.get_localized_name()
            favorite = "★" if product.favorite else " "
            featured = "[특집]" if product.featured else ""
            
            time_min = product.cooking_time // 60
            time_sec = product.cooking_time % 60
            time_str = f"{time_min}분 {time_sec}초" if time_min > 0 else f"{time_sec}초"
            
            print(f"{i}. {favorite} {name} {featured} - {time_str}")
            
        print("\n0. 이전 메뉴")
        
        choice = input("\n선택: ").strip()
        if choice == "0":
            self.pop_context()
            self.category_menu()
            return
            
        try:
            index = int(choice) - 1
            if 0 <= index < len(products):
                self.product_detail_menu(products[index])
            else:
                print("\n잘못된 선택입니다.")
                time.sleep(1.5)
                self.product_list_menu(category)
        except ValueError:
            print("\n숫자를 입력하세요.")
            time.sleep(1.5)
            self.product_list_menu(category)
            
    def favorite_products_menu(self) -> None:
        """즐겨찾기 제품 메뉴"""
        self.push_context("즐겨찾기 제품")
        self.display_menu_header("즐겨찾기 제품")
        
        favorites = self.app.get_favorite_products()
        
        if not favorites:
            print("즐겨찾기한 제품이 없습니다.")
            print("메인 메뉴에서 제품을 선택하고 즐겨찾기에 추가해 보세요.")
            print("\n0. 이전 메뉴")
            choice = input("\n선택: ").strip()
            if choice == "0":
                self.pop_context()
                self.main_menu()
            return
            
        # 목록 표시 및 선택 로직
        for i, product in enumerate(favorites, 1):
            print(f"{i}. {product.get_localized_name()} ({product.category})")
            
        print("\n0. 이전 메뉴")
        choice = input("\n선택: ").strip()
        
        if choice == "0":
            self.pop_context()
            self.main_menu()
            return
            
        try:
            index = int(choice) - 1
            if 0 <= index < len(favorites):
                self.product_detail_menu(favorites[index])
            else:
                print("\n잘못된 선택입니다.")
                time.sleep(1.5)
                self.favorite_products_menu()
        except ValueError:
            print("\n숫자를 입력하세요.")
            time.sleep(1.5)
            self.favorite_products_menu()
            
    def recent_products_menu(self) -> None:
        """최근 사용 제품 메뉴"""
        self.push_context("최근 사용 제품")
        self.display_menu_header("최근 사용 제품")
        
        recents = self.app.get_recent_products()
        
        if not recents:
            print("최근 사용한 제품이 없습니다.")
            print("\n0. 이전 메뉴")
            choice = input("\n선택: ").strip()
            if choice == "0":
                self.pop_context()
                self.main_menu()
            return
            
        # 목록 표시 및 선택 로직
        for i, product in enumerate(recents, 1):
            name = product.get_localized_name()
            favorite = "★" if product.favorite else " "
            
            time_min = product.cooking_time // 60
            time_sec = product.cooking_time % 60
            time_str = f"{time_min}분 {time_sec}초" if time_min > 0 else f"{time_sec}초"
            
            print(f"{i}. {favorite} {name} - {time_str}")
            
        print("\n0. 이전 메뉴")
        choice = input("\n선택: ").strip()
        
        if choice == "0":
            self.pop_context()
            self.main_menu()
            return
            
        try:
            index = int(choice) - 1
            if 0 <= index < len(recents):
                self.product_detail_menu(recents[index])
            else:
                print("\n잘못된 선택입니다.")
                time.sleep(1.5)
                self.recent_products_menu()
        except ValueError:
            print("\n숫자를 입력하세요.")
            time.sleep(1.5)
            self.recent_products_menu()
            
    def search_products(self) -> None:
        """제품 검색 메뉴"""
        self.push_context("제품 검색")
        self.display_menu_header("제품 검색")
        
        print("검색어를 입력하세요 (뒤로 가려면 빈 입력):")
        query = input().strip()
        
        if not query:
            self.pop_context()
            self.main_menu()
            return
            
        self.display_search_results(query)
        
    def display_search_results(self, query: str) -> None:
        """검색 결과 표시
        
        Args:
            query (str): 검색어
        """
        self.push_context("검색 결과", {'query': query})
        self.display_menu_header(f"'{query}' 검색 결과")
        
        results = self.app.search_products(query)
        
        if not results:
            print(f"'{query}'에 대한 검색 결과가 없습니다.")
            print("\n1. 다시 검색")
            print("0. 이전 메뉴")
            
            choice = input("\n선택: ").strip()
            if choice == "1":
                self.pop_context()  # 검색 결과 컨텍스트 제거
                self.search_products()
            else:
                self.pop_context()  # 검색 결과 컨텍스트 제거
                self.pop_context()  # 검색 메뉴 컨텍스트 제거
                self.main_menu()
            return
            
        # 검색 결과 표시 및 선택 로직
        for i, product in enumerate(results, 1):
            print(f"{i}. {product.get_localized_name()} ({product.category})")
            
        print("\n0. 이전 메뉴")
        choice = input("\n선택: ").strip()
        
        if choice == "0":
            self.pop_context()  # 검색 결과 컨텍스트 제거
            self.search_products()
            return
            
        try:
            index = int(choice) - 1
            if 0 <= index < len(results):
                self.product_detail_menu(results[index])
            else:
                print("\n잘못된 선택입니다.")
                time.sleep(1.5)
                self.display_search_results(query)
        except ValueError:
            print("\n숫자를 입력하세요.")
            time.sleep(1.5)
            self.display_search_results(query)
            
    def product_detail_menu(self, product: Product) -> None:
        """제품 상세 정보 메뉴
        
        Args:
            product (Product): 제품 객체
        """
        self.push_context("제품 상세", {'product': product, 'category': product.category})
        self.display_menu_header(f"{product.get_localized_name()} 상세 정보")
        
        print(f"이름: {product.get_localized_name()}")
        print(f"카테고리: {product.category}")
        print(f"조리 시간: {format_time(product.cooking_time)}")
        print(f"즐겨찾기: {'예' if product.favorite else '아니오'}")
        print(f"마지막 사용: {format_datetime(product.last_used) if product.last_used else '사용 기록 없음'}")
        
        if product.cooking_instructions:
            print("\n[조리 방법]")
            for i, instruction in enumerate(product.cooking_instructions, 1):
                print(f"{i}. {instruction}")
                
        print("\n1. 타이머 시작")
        print(f"2. {'즐겨찾기 해제' if product.favorite else '즐겨찾기 추가'}")
        print("0. 이전 메뉴")
        
        choice = input("\n선택: ").strip()
        if choice == "0":
            # 이전 메뉴로 돌아가기
            previous_menu = self.get_previous_menu_for_product(product)
            previous_menu()
        elif choice == "1":
            self.start_product_timer(product)
        elif choice == "2":
            new_status = self.app.toggle_favorite(product.id)
            status_text = "추가되었습니다" if new_status else "해제되었습니다"
            print(f"\n즐겨찾기가 {status_text}.")
            time.sleep(1.5)
            self.product_detail_menu(product)
        else:
            print("\n잘못된 선택입니다.")
            time.sleep(1.5)
            self.product_detail_menu(product)
            
    def get_previous_menu_for_product(self, product: Product) -> Callable[[], None]:
        """제품 객체에 맞는 이전 메뉴 함수 반환
        
        Args:
            product (Product): 제품 객체
            
        Returns:
            Callable: 이전 메뉴 함수
        """
        previous_context = self.pop_context()
        
        # 이전 컨텍스트 기반으로 적절한 메뉴로 이동
        def go_to_previous_menu():
            if previous_context and 'menu' in previous_context:
                if previous_context['menu'] == "제품 목록":
                    category = product.category
                    if 'category' in previous_context['data']:
                        category = previous_context['data']['category']
                    self.product_list_menu(category)
                elif previous_context['menu'] == "즐겨찾기 제품":
                    self.favorite_products_menu()
                elif previous_context['menu'] == "최근 사용 제품":
                    self.recent_products_menu()
                elif previous_context['menu'] == "검색 결과":
                    # 검색 결과로 돌아가려면 이전 검색어 필요
                    if 'query' in previous_context['data']:
                        self.display_search_results(previous_context['data']['query'])
                    else:
                        self.main_menu()
                else:
                    self.main_menu()
            else:
                self.category_menu()
        
        return go_to_previous_menu
        
    def start_product_timer(self, product: Product) -> None:
        """제품 타이머 시작
        
        Args:
            product (Product): 타이머를 시작할 제품 객체
        """
        self.push_context("타이머", {'product': product})
        name = product.get_localized_name()
        self.display_menu_header(f"{name} 타이머")
        
        print(f"{name}의 타이머를 시작합니다.")
        print(f"조리 시간: {product.cooking_time//60}분 {product.cooking_time%60}초")
        print("\n타이머를 시작하려면 Enter 키를 누르세요. (취소: ESC)")
        
        key = msvcrt.getch()
        if key == b'\r':  # Enter 키
            success = self.app.start_product_timer(product.id)
            if success:
                print("\n타이머가 시작되었습니다!")
                input("\n아무 키나 눌러 메인 메뉴로 돌아가기...")
                self.main_menu()
            else:
                print("\n타이머 시작 중 오류가 발생했습니다.")
                time.sleep(1.5)
                self.product_detail_menu(product)
        elif key == b'\x1b':  # ESC 키
            self.product_detail_menu(product)
        else:
            print("\n잘못된 키입니다. 다시 시도하세요.")
            time.sleep(1.5)
            self.start_product_timer(product)
            
    def settings_menu(self) -> None:
        """설정 메뉴 표시"""
        self.display_menu_header("설정")
        
        print("1. 알림 설정")
        print("2. 언어 설정")
        print("0. 이전 메뉴")
        
        choice = input("\n선택: ").strip()
        if choice == "0":
            self.main_menu()
        elif choice == "1":
            self.notification_settings()
        elif choice == "2":
            self.language_settings()
        else:
            print("\n잘못된 선택입니다.")
            time.sleep(1.5)
            self.settings_menu()
            
    def notification_settings(self) -> None:
        """알림 설정 메뉴"""
        self.display_menu_header("알림 설정")
        
        settings = self.app.settings.get_settings()
        
        print(f"1. 소리 알림: {'켜짐' if settings.get('sound_enabled', True) else '꺼짐'}")
        print(f"2. 데스크톱 알림: {'켜짐' if settings.get('desktop_notification', True) else '꺼짐'}")
        print("0. 이전 메뉴")
        
        choice = input("\n선택: ").strip()
        if choice == "0":
            self.settings_menu()
        elif choice == "1":
            self.app.settings.toggle_setting('sound_enabled')
            self.notification_settings()
        elif choice == "2":
            self.app.settings.toggle_setting('desktop_notification')
            self.notification_settings()
        else:
            print("\n잘못된 선택입니다.")
            time.sleep(1.5)
            self.notification_settings()
            
    def language_settings(self) -> None:
        """언어 설정 메뉴"""
        self.display_menu_header("언어 설정")
        
        settings = self.app.settings.get_settings()
        current_lang = settings.get('language', 'ko')
        
        print(f"1. 한국어 {'(현재)' if current_lang == 'ko' else ''}")
        print(f"2. English {'(Current)' if current_lang == 'en' else ''}")
        print("0. 이전 메뉴")
        
        choice = input("\n선택: ").strip()
        if choice == "0":
            self.settings_menu()
        elif choice == "1":
            self.app.settings.set_setting('language', 'ko')
            self.language_settings()
        elif choice == "2":
            self.app.settings.set_setting('language', 'en')
            self.language_settings()
        else:
            print("\n잘못된 선택입니다.")
            time.sleep(1.5)
            self.language_settings()
            
    def exit_app(self) -> None:
        """앱 종료"""
        self.clear_screen()
        self.display_header()
        
        print("K-Food 타이머를 종료합니다.")
        print("데이터를 저장하는 중...")
        
        if self.app.save_all_data():
            print("데이터가 성공적으로 저장되었습니다.")
        else:
            print("데이터 저장 중 일부 오류가 발생했습니다.")
            
        print("\n이용해 주셔서 감사합니다!")
        time.sleep(2)
        sys.exit(0)

    def notify_timer_complete(self, timer):
        """타이머 완료 알림
        
        Args:
            timer: 완료된 타이머 객체
        """
        title = "타이머 완료!"
        message = f"{timer.name} 조리가 완료되었습니다."
        
        # 알림 관리자를 통해 알림 전송
        self.notification_manager.notify(title, message)
        
    def display_timer(self, timer):
        """타이머 화면 표시
        
        Args:
            timer: 표시할 타이머 객체
        """
        # 타이머 표시 로직...
        # 이 부분은 기존 코드를 유지하되, utils 모듈의 함수를 사용하도록 수정
        
    # 기타 UI 관련 메서드들... 