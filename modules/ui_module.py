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

# 분리된 모듈 import
from modules.utils import clear_screen, format_time, format_datetime, get_current_datetime
from modules.menu_module import MenuManager
from modules.notification_module import NotificationManager

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


class UIManager:
    """사용자 인터페이스 관리 클래스
    
    이 클래스는 K-Food Timer 애플리케이션의 콘솔 기반 사용자 인터페이스를 관리합니다.
    메뉴 시스템, 사용자 입력 처리, 타이머 표시 및 관리 기능을 제공합니다.
    """
    
    def __init__(self, app):
        """UI 관리자 초기화
        
        Args:
            app: 메인 애플리케이션 객체 (앱의 모든 관리자 모듈에 접근 가능)
        """
        self.app = app
        self.current_menu = "main"  # 현재 활성화된 메뉴 상태
        self.timer_display_thread = None  # 타이머 표시용 스레드
        
        # 메뉴 관리자 초기화
        self.menu_manager = MenuManager(app)
        self.menu_manager.set_ui_manager(self)
        
        # 알림 관리자 초기화
        self.notification_manager = NotificationManager(app.settings_manager)
        
    def start(self):
        """UI 시작 - 환영 메시지 표시하고 메인 메뉴 진입"""
        self.show_welcome_message()
        self.main_menu()
        
    def show_welcome_message(self):
        """환영 메시지 표시 - 앱 타이틀과 현재 시간을 포함하는 시작 화면"""
        clear_screen()
        print("\n" + "="*50)
        print("\n      K-Food Timer - 한국 간편식품 타이머 앱      ")
        print("\n" + "="*50)
        print(f"\n현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n간편식품 조리를 위한 편리한 타이머 앱입니다.")
        print("다양한 한국 간편식품의 정확한 조리 시간을 관리하세요.\n")
        
    def clear_screen(self):
        """화면 지우기 - 운영체제에 따라 적절한 명령어 사용"""
        os.system(CLEAR_COMMAND)  # 미리 정의된 명령 사용
    
    def display_menu_header(self, title):
        """메뉴 헤더 표시 - 화면을 지우고 메뉴 제목 표시
        
        Args:
            title (str): 표시할 메뉴 제목
        """
        clear_screen()  # utils 모듈의 함수 사용
        print("\n" + "=" * 50)
        print(f"{title:^50}")
        print("=" * 50 + "\n")
    
    @staticmethod
    @lru_cache(maxsize=128)
    def format_cooking_time(seconds):
        """요리 시간을 분과 초로 포맷팅
        
        Args:
            seconds (int): 초 단위 시간
            
        Returns:
            str: '분m 초s' 형태의 포맷된 문자열
        """
        minutes, secs = divmod(seconds, 60)
        return f"{minutes}분 {secs}초"
    
    def display_product_info(self, product, include_index=False, index=None):
        """제품 정보 출력 - 제품 정보를 포맷에 맞게 표시
        
        Args:
            product: 표시할 제품 객체
            include_index (bool): 인덱스 표시 여부
            index (int, optional): 표시할 인덱스 번호
        """
        # 즐겨찾기 여부에 따라 별표 표시
        favorite_symbol = "★" if product.favorite else " "
        
        # 인덱스 포함 여부에 따라 접두사 설정
        prefix = f"{index}. " if include_index else ""
        
        # 제품 기본 정보 표시 (포맷팅 함수 사용)
        formatted_time = self.format_cooking_time(product.cooking_time)
        print(f"{prefix}[{favorite_symbol}] {product.name} ({product.category}, {formatted_time})")
        
        # 마지막 사용 시간이 있다면 표시
        if hasattr(product, 'last_used') and product.last_used:
            print(f"   마지막 사용: {product.last_used.strftime('%Y-%m-%d %H:%M:%S')}")
    
    @staticmethod
    def get_user_input(prompt="선택하세요: "):
        """사용자 입력 받기 - 프롬프트 표시 후 입력값 반환
        
        Args:
            prompt (str): 표시할 프롬프트 메시지
            
        Returns:
            str: 사용자 입력값 (공백 제거됨)
        """
        return input(f"\n{prompt}").strip()
    
    @staticmethod
    def show_message_and_wait(message="잘못된 선택입니다."):
        """메시지 표시 후 사용자 입력 대기
        
        Args:
            message (str): 표시할 메시지
        """
        input(f"\n{message} 엔터 키를 눌러 계속하세요...")
    
    def select_item_from_menu(self, items, prompt="선택하세요 (번호): ", empty_message="항목이 없습니다.", back_menu_name="이전 메뉴"):
        """메뉴 목록에서 항목 선택 처리
        
        Args:
            items (list): 선택 가능한 항목 목록
            prompt (str): 선택 프롬프트 메시지
            empty_message (str): 항목이 없을 때 표시할 메시지
            back_menu_name (str): 돌아갈 메뉴 이름
            
        Returns:
            int: 선택한 항목 인덱스 또는 -1 (돌아가기) 또는 None (잘못된 선택)
        """
        # 항목이 없는 경우 처리
        if not items:
            print(f"\n{empty_message}")
            self.show_message_and_wait(f"엔터 키를 눌러 {back_menu_name}로 돌아가세요...")
            return -1
        
        # 돌아가기 옵션 표시    
        print(f"\n0. {back_menu_name}로 돌아가기")
        
        # 사용자 선택 받기
        choice = self.get_user_input(prompt)
        
        # 돌아가기 선택
        if choice == "0":
            return -1
        
        # 숫자 입력 처리
        try:
            selected_idx = int(choice) - 1
            if 0 <= selected_idx < len(items):
                return selected_idx
            else:
                # 유효 범위 벗어남
                self.show_message_and_wait()
                return None
        except ValueError:
            # 숫자가 아닌 입력
            self.show_message_and_wait("숫자를 입력해주세요.")
            return None
    
    def get_active_timers_info(self):
        """활성화된 타이머 정보 문자열 생성
        
        Returns:
            str: 활성 타이머 정보를 포함한 문자열, 없으면 빈 문자열
        """
        active_timers = self.app.timer_manager.get_active_timers()
        if not active_timers:
            return ""
            
        # 리스트 컴프리헨션 활용
        timer_info = ["\n=== 활성 타이머 ==="] + [
            f"- {timer.name}: {timer.get_formatted_time()} {'[일시정지]' if timer.is_paused else '[실행중]'}"
            for _, timer in active_timers.items()
        ]
        
        return "\n".join(timer_info) + "\n"
            
    def main_menu(self):
        """메인 메뉴 표시 및 처리"""
        self.current_menu = "main"
        
        while True:
            # 메뉴 헤더 표시
            self.display_menu_header("메인 메뉴")
            
            # 활성 타이머 정보 표시 (있을 경우)
            active_timers_info = self.get_active_timers_info()
            if active_timers_info:
                print(active_timers_info)
            
            # 메인 메뉴 옵션 표시
            options = [
                "타이머 시작",
                "제품 관리",
                "설정",
                "도움말",
                "종료"
            ]
            
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")
                
            # 사용자 선택 처리
            choice = self.get_user_input("\n선택하세요 (1-5): ")
            
            if choice == "1":
                clear_screen()
                self.timer_menu()
            elif choice == "2":
                clear_screen()
                self.product_menu()
            elif choice == "3":
                clear_screen()
                self.settings_menu()
            elif choice == "4":
                clear_screen()
                self.help_menu()
            elif choice == "5":
                self.app.exit()
            else:
                self.show_message_and_wait("잘못된 선택입니다. 1-5 사이의 숫자를 입력하세요.")
                
    def timer_menu(self):
        """타이머 메뉴 - 타이머 시작 관련 기능 제공"""
        self.current_menu = "timer"
        
        while True:
            self.display_menu_header("타이머 시작")
            
            # 타이머 시작 방법 선택 메뉴
            print("1. 제품 목록에서 선택")
            print("2. 카테고리별 제품 선택")
            print("3. 즐겨찾기 제품에서 선택")
            print("4. 최근 사용한 제품에서 선택")
            print("0. 메인 메뉴로 돌아가기")
            
            choice = self.get_user_input("\n선택하세요 (0-4): ")
            
            if choice == "1":
                clear_screen()
                self.product_list_menu()
            elif choice == "2":
                clear_screen()
                self.category_menu()
            elif choice == "3":
                clear_screen()
                self.favorite_products_menu()
            elif choice == "4":
                clear_screen()
                self.recent_products_menu()
            elif choice == "0":
                clear_screen()
                break
            else:
                self.show_message_and_wait("잘못된 선택입니다. 0-4 사이의 숫자를 입력하세요.")
    
    def product_menu(self):
        """제품 관리 메뉴 - 제품 관련 기능 제공"""
        self.current_menu = "product"
        
        while True:
            self.menu_manager.display_menu_header("제품 관리")
            
            print("1. 제품 목록 보기")
            print("2. 카테고리별 제품 보기")
            print("3. 즐겨찾기 제품 보기")
            print("4. 최근 사용한 제품 보기")
            print("0. 메인 메뉴로 돌아가기")
            
            choice = self.menu_manager.get_user_input("\n선택하세요 (0-4): ")
            
            if choice == "1":
                self.product_list_menu()
            elif choice == "2":
                self.category_menu()
            elif choice == "3":
                self.favorite_products_menu()
            elif choice == "4":
                self.recent_products_menu()
            elif choice == "0":
                break
            else:
                self.menu_manager.show_message_and_wait("잘못된 선택입니다. 0-4 사이의 숫자를 입력하세요.")
    
    def help_menu(self):
        """도움말 메뉴 - 앱 사용 안내"""
        self.current_menu = "help"
        
        self.menu_manager.display_menu_header("도움말")
        
        help_text = """
K-Food Timer 앱 사용 안내

1. 타이머 시작
   - 제품 목록에서 원하는 제품을 선택하여 타이머를 시작할 수 있습니다.
   - 카테고리별로 제품을 찾아 타이머를 시작할 수 있습니다.
   - 즐겨찾기나 최근 사용한 제품에서 빠르게 선택할 수 있습니다.

2. 제품 관리
   - 제품 목록을 확인하고 상세 정보를 볼 수 있습니다.
   - 즐겨찾기 기능으로 자주 사용하는 제품을 관리할 수 있습니다.

3. 설정
   - 소리 알림, 테마, 언어 등의 앱 설정을 변경할 수 있습니다.

4. 팁
   - 타이머가 실행 중일 때는 메인 메뉴에서 상태를 확인할 수 있습니다.
   - 제품 상세 정보에서 조리 방법을 확인할 수 있습니다.
"""
        print(help_text)
        
        self.menu_manager.show_message_and_wait("메인 메뉴로 돌아가려면 Enter 키를 누르세요...")
    
    def display_product_list(self, products):
        """제품 목록 표시 - 제네레이터 패턴 적용
        
        Args:
            products (list): 표시할 제품 목록
        """
        for i, product in enumerate(products, 1):
            self.display_product_info(product, True, i)
                
    def product_list_menu(self):
        """제품 목록 메뉴 - 모든 등록된 제품 표시 및 선택 처리"""
        self.current_menu = "product_list"
        
        while True:
            # 메뉴 헤더 표시
            self.display_menu_header("제품 목록")
            
            # 전체 제품 목록 가져오기
            products = self.app.product_manager.get_all_products()
            if not products:
                print("\n등록된 제품이 없습니다.")
                self.show_message_and_wait(BACK_TO_MAIN_MSG)
                break
                
            # 제품 목록 표시 (별도 함수 사용)
            self.display_product_list(products)
                
            # 제품 선택 처리
            selected_idx = self.select_item_from_menu(products, "제품을 선택하세요 (번호): ", back_menu_name="메인 메뉴")
            if selected_idx == -1:
                break
            elif selected_idx is not None:
                # 화면 지우고 제품 상세 메뉴로 이동
                self.product_detail_menu(products[selected_idx])
    
    @lru_cache(maxsize=16)       
    def get_categories(self):
        """카테고리 목록 가져오기 (캐싱 적용)
        
        Returns:
            list: 카테고리 목록
        """
        return self.app.product_manager.get_categories()
                
    def category_menu(self):
        """카테고리 메뉴 - 제품 카테고리 목록 표시 및 선택 처리"""
        self.current_menu = "category"
        
        while True:
            # 메뉴 헤더 표시
            self.display_menu_header("카테고리 목록")
            
            # 카테고리 목록 가져오기 (캐싱된 메서드 사용)
            categories = self.get_categories()
            if not categories:
                print("\n등록된 카테고리가 없습니다.")
                self.show_message_and_wait(BACK_TO_MAIN_MSG)
                break
                
            # 카테고리 목록 표시 (리스트 컴프리헨션 활용)
            [print(f"{i}. {category}") for i, category in enumerate(categories, 1)]
                
            # 카테고리 선택 처리
            selected_idx = self.select_item_from_menu(
                categories, 
                "카테고리를 선택하세요 (번호): ", 
                "등록된 카테고리가 없습니다.", 
                "메인 메뉴"
            )
            
            if selected_idx == -1:
                break
            elif selected_idx is not None:
                # 화면 지우고 카테고리별 제품 메뉴로 이동
                clear_screen()
                self.category_products_menu(categories[selected_idx])
                
    def category_products_menu(self, category):
        """카테고리별 제품 목록 메뉴 - 특정 카테고리의 제품 표시 및 선택 처리
        
        Args:
            category (str): 제품 카테고리 이름
        """
        while True:
            # 메뉴 헤더 표시
            self.display_menu_header(f"{category} 제품 목록")
            
            # 해당 카테고리의 제품 목록 가져오기
            category_products = self.app.product_manager.get_products_by_category(category)
            if not category_products:
                print(f"\n{category} 카테고리에 등록된 제품이 없습니다.")
                self.show_message_and_wait(MENU_BACK_TO_CATEGORY_MSG)
                break
                
            # 제품 목록 표시 (별도 함수 사용)
            self.display_product_list(category_products)
                
            # 제품 선택 처리
            selected_idx = self.select_item_from_menu(
                category_products, 
                "제품을 선택하세요 (번호): ", 
                back_menu_name="카테고리 메뉴"
            )
            
            if selected_idx == -1:
                break
            elif selected_idx is not None:
                self.product_detail_menu(category_products[selected_idx])
                
    @lru_cache(maxsize=1)            
    def get_favorite_products(self):
        """즐겨찾기 제품 목록 가져오기 (캐싱 적용)
        
        Returns:
            list: 즐겨찾기 제품 목록
        """
        return self.app.product_manager.get_favorite_products()
                
    def favorite_products_menu(self):
        """즐겨찾기 제품 목록 메뉴 - 즐겨찾기된 제품 표시 및 선택 처리"""
        self.current_menu = "favorites"
        
        while True:
            # 메뉴 헤더 표시
            self.display_menu_header("즐겨찾기 제품 목록")
            
            # 즐겨찾기 제품 목록 가져오기 (캐싱된 메서드 사용)
            favorite_products = self.get_favorite_products()
            # 캐시 무효화 (제품 상태가 변경될 수 있으므로)
            self.get_favorite_products.cache_clear()
            
            if not favorite_products:
                print("\n즐겨찾기한 제품이 없습니다.")
                self.show_message_and_wait(BACK_TO_MAIN_MSG)
                break
                
            # 제품 목록 표시 (별도 함수 사용)
            self.display_product_list(favorite_products)
                
            # 제품 선택 처리
            selected_idx = self.select_item_from_menu(
                favorite_products, 
                "제품을 선택하세요 (번호): ", 
                back_menu_name="메인 메뉴"
            )
            
            if selected_idx == -1:
                break
            elif selected_idx is not None:
                self.product_detail_menu(favorite_products[selected_idx])
    
    @lru_cache(maxsize=1)
    def get_recent_products(self):
        """최근 사용 제품 목록 가져오기 (캐싱 적용)
        
        Returns:
            list: 최근 사용 제품 목록
        """
        return self.app.product_manager.get_recent_products()
                
    def recent_products_menu(self):
        """최근 사용 제품 목록 메뉴 - 최근 사용한 제품 표시 및 선택 처리"""
        self.current_menu = "recent"
        
        while True:
            # 메뉴 헤더 표시
            self.display_menu_header("최근 사용한 제품 목록")
            
            # 최근 사용 제품 목록 가져오기 (캐싱된 메서드 사용)
            recent_products = self.get_recent_products()
            # 캐시 무효화 (목록이 변경될 수 있으므로)
            self.get_recent_products.cache_clear()
            
            if not recent_products:
                print("\n최근 사용한 제품이 없습니다.")
                self.show_message_and_wait(BACK_TO_MAIN_MSG)
                break
                
            # 제품 목록 표시 (별도 함수 사용)
            self.display_product_list(recent_products)
                
            # 제품 선택 처리
            selected_idx = self.select_item_from_menu(
                recent_products, 
                "제품을 선택하세요 (번호): ", 
                back_menu_name="메인 메뉴"
            )
            
            if selected_idx == -1:
                break
            elif selected_idx is not None:
                self.product_detail_menu(recent_products[selected_idx])
    
    @staticmethod
    @lru_cache(maxsize=32)
    def format_product_detail(product):
        """제품 상세 정보 문자열 생성
        
        Args:
            product: 대상 제품 객체
            
        Returns:
            str: 포맷된 제품 상세 정보
        """
        favorite_symbol = "★" if product.favorite else "☆"
        
        minutes, seconds = divmod(product.cooking_time, 60)
        formatted_time = f"{minutes}분 {seconds}초"
        
        # 리스트 컴프리헨션으로 변경
        details = [
            f"\n- 제품명: {product.name}",
            f"- 카테고리: {product.category}",
            f"- 조리 시간: {formatted_time}",
            f"- 즐겨찾기: {favorite_symbol}"
        ]
        
        if product.description:
            details.append(f"- 설명: {product.description}")
            
        if product.instructions:
            details.append("\n[조리 방법]")
            # 리스트 컴프리헨션 활용
            details.extend(f"{i}. {instruction}" for i, instruction in enumerate(product.instructions, 1))
                
        return "\n".join(details)
                
    def product_detail_menu(self, product):
        """제품 상세 정보 메뉴 - 선택한 제품의 상세 정보 및 기능 제공
        
        Args:
            product: 표시할 제품 객체
        """
        self.current_menu = "product_detail"
        
        # 캐시를 이 제품에 대해 무효화 (변경될 수 있으므로)
        self.format_product_detail.cache_clear()
        
        # 메뉴 옵션 사전 생성
        menu_text = "\n===== 기능 =====\n1. 타이머 시작\n%s\n0. 이전 메뉴로 돌아가기"
        
        while True:
            # 메뉴 헤더 표시
            self.display_menu_header(f"{product.name} 상세 정보")
            
            # 제품 상세 정보 표시
            print(self.format_product_detail(product))
            
            # 제품 기능 메뉴 표시 (포맷팅 활용)
            print(menu_text % f"2. {'즐겨찾기 해제' if product.favorite else '즐겨찾기 추가'}")
            
            # 사용자 선택 처리
            choice = self.get_user_input()
            
            if choice == "1":
                # 타이머 시작
                self.start_product_timer(product)
            elif choice == "2":
                # 즐겨찾기 상태 토글
                product.toggle_favorite()
                self.app.product_manager.save_products()
                # 즐겨찾기가 변경되었으므로 캐시 무효화
                self.format_product_detail.cache_clear()
                self.get_favorite_products.cache_clear()
            elif choice == "0":
                # 이전 메뉴로 돌아가기
                break
            else:
                self.show_message_and_wait()
                
    def start_product_timer(self, product):
        """제품 타이머 시작 - 선택한 제품의 타이머 생성 및 시작
        
        Args:
            product: 타이머를 시작할 제품 객체
        """
        # 제품 사용 기록 업데이트
        product.mark_as_used()
        self.app.product_manager.save_products()
        
        # 최근 사용 제품 목록에 추가
        self.app.settings_manager.add_recent_product(product.id)
        self.app.settings_manager.save_settings()
        
        # 최근 제품 캐시 무효화
        self.get_recent_products.cache_clear()
        
        # 타이머 생성 및 시작
        timer_id = self.app.timer_manager.create_timer(
            duration=product.cooking_time,
            name=f"{product.name} 타이머"
        )
        
        # 타이머 활성화
        self.app.timer_manager.start_timer(timer_id)
        
        # 시작 메시지 표시
        self.show_message_and_wait(f"{product.name} 타이머가 시작되었습니다.")
        
    def timer_management_menu(self):
        """타이머 관리 메뉴 - 활성화된 타이머 목록 및 관리 기능 제공"""
        self.current_menu = "timer"
        
        # 타이머 관리 메뉴 옵션
        timer_menu_text = "\n===== 기능 =====\n1. 타이머 일시정지/재개\n2. 타이머 정지\n0. 메인 메뉴로 돌아가기"
        
        while True:
            # 메뉴 헤더 표시
            self.display_menu_header("타이머 관리")
            
            # 활성 타이머 목록 가져오기
            active_timers = self.app.timer_manager.get_active_timers()
            if not active_timers:
                print("\n현재 실행 중인 타이머가 없습니다.")
                self.show_message_and_wait(BACK_TO_MAIN_MSG)
                break
                
            # 활성 타이머 목록 표시 (리스트 컴프리헨션 적용)
            timer_ids = list(active_timers.keys())
            [
                print(f"{i}. {active_timers[timer_id].name} - {active_timers[timer_id].get_formatted_time()} {'[일시정지]' if active_timers[timer_id].is_paused else '[실행중]'}")
                for i, timer_id in enumerate(timer_ids, 1)
            ]
                
            # 타이머 관리 기능 메뉴 표시
            print(timer_menu_text)
            
            # 사용자 선택 처리
            choice = self.get_user_input()
            
            if choice == "0":
                # 메인 메뉴로 돌아가기
                break
                
            if choice in ["1", "2"]:
                # 타이머 번호 선택 처리
                timer_input = self.get_user_input("타이머 번호를 선택하세요: ")
                
                try:
                    # 타이머 인덱스 계산
                    timer_idx = int(timer_input) - 1
                    
                    # 유효한 타이머 인덱스인지 확인
                    if 0 <= timer_idx < len(timer_ids):
                        timer_id = timer_ids[timer_idx]
                        timer = active_timers[timer_id]
                        
                        if choice == "1":
                            # 타이머 일시정지/재개
                            self.toggle_timer_pause_state(timer_id, timer)
                                
                        elif choice == "2":
                            # 타이머 정지
                            self.app.timer_manager.stop_timer(timer_id)
                            self.show_message_and_wait(f"{timer.name}가 정지되었습니다.")
                            
                    else:
                        # 유효하지 않은 타이머 번호
                        self.show_message_and_wait("잘못된 타이머 번호입니다.")
                except ValueError:
                    # 숫자가 아닌 입력
                    self.show_message_and_wait("숫자를 입력해주세요.")
            else:
                # 유효하지 않은 메뉴 선택
                self.show_message_and_wait()
    
    def toggle_timer_pause_state(self, timer_id, timer):
        """타이머 일시정지/재개 상태 전환
        
        Args:
            timer_id (str): 타이머 ID
            timer (Timer): 타이머 객체
        """
        if timer.is_paused:
            # 일시정지 상태일 경우 재개
            self.app.timer_manager.resume_timer(timer_id)
            self.show_message_and_wait(f"{timer.name}가 재개되었습니다.")
        else:
            # 실행 중일 경우 일시정지
            self.app.timer_manager.pause_timer(timer_id)
            self.show_message_and_wait(f"{timer.name}가 일시정지되었습니다.")
                
    def settings_menu(self):
        """설정 메뉴 - 앱 설정 변경 기능 제공"""
        self.current_menu = "settings"
        
        # 설정 메뉴 옵션 텍스트 미리 정의
        settings_menu_template = """1. 소리 알림: {sound}
2. 알림: {notification}
3. 테마: {theme}
4. 언어: {language}
5. 기본 설정으로 초기화
0. 메인 메뉴로 돌아가기"""
        
        while True:
            # 메뉴 헤더 표시
            self.display_menu_header("설정")
            
            # 현재 설정값 가져오기
            settings_mgr = self.app.settings_manager
            
            # 설정 메뉴 표시 (format 메서드 활용)
            print(settings_menu_template.format(
                sound="켜짐" if settings_mgr.get_setting("sound_enabled") else "꺼짐",
                notification="켜짐" if settings_mgr.get_setting("notification_enabled") else "꺼짐",
                theme=settings_mgr.get_setting("theme"),
                language=settings_mgr.get_setting("language")
            ))
            
            # 사용자 선택 처리
            choice = self.get_user_input()
            
            if choice == "1":
                # 소리 알림 설정 토글
                settings_mgr.set_setting("sound_enabled", not settings_mgr.get_setting("sound_enabled"))
                settings_mgr.save_settings()
                
            elif choice == "2":
                # 알림 설정 토글
                settings_mgr.set_setting("notification_enabled", not settings_mgr.get_setting("notification_enabled"))
                settings_mgr.save_settings()
                
            elif choice == "3":
                # 테마 변경
                current_theme = settings_mgr.get_setting("theme")
                settings_mgr.set_setting("theme", "dark" if current_theme == "light" else "light")
                settings_mgr.save_settings()
                
            elif choice == "4":
                # 언어 설정 변경
                self.change_language_setting()
                    
            elif choice == "5":
                # 기본 설정으로 초기화
                self.reset_settings_to_defaults()
                    
            elif choice == "0":
                # 메인 메뉴로 돌아가기
                break
                
            else:
                # 유효하지 않은 메뉴 선택
                self.show_message_and_wait()
    
    def change_language_setting(self):
        """언어 설정 변경 - 지원되는 언어 코드 입력 처리"""
        # 지원되는 언어 목록
        supported_languages = {"ko": "한국어", "en": "영어"}
        
        # 현재 선택된 언어 가져오기
        current_lang = self.app.settings_manager.get_setting("language")
        
        # 언어 선택 메뉴 표시 (리스트 컴프리헨션 활용)
        print("\n=== 언어 설정 ===")
        [print(f"{code}: {name} {'[현재]' if code == current_lang else ''}") 
         for code, name in supported_languages.items()]
        
        new_language = self.get_user_input("언어 코드를 입력하세요 (ko, en): ").lower()
        
        # 지원되는 언어 코드인지 확인
        if new_language in supported_languages:
            self.app.settings_manager.set_setting("language", new_language)
            self.app.settings_manager.save_settings()
        else:
            self.show_message_and_wait("지원하지 않는 언어 코드입니다.")
    
    def reset_settings_to_defaults(self):
        """설정을 기본값으로 초기화 - 확인 후 처리"""
        # 사용자 확인 요청
        confirm = self.get_user_input("모든 설정을 기본값으로 초기화하시겠습니까? (y/n): ").lower()
        
        if confirm == "y":
            # 설정 초기화 및 저장
            self.app.settings_manager.reset_to_defaults()
            self.app.settings_manager.save_settings()
            self.show_message_and_wait("설정이 초기화되었습니다.")
                
    def exit_app(self):
        """앱 종료 - 종료 메시지 표시 후 앱 종료 처리"""
        print("\n앱을 종료합니다...")
        self.app.exit()

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