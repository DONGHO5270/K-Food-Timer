#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K-Food Timer 애플리케이션의 메뉴 관리 모듈

이 모듈은 애플리케이션의 다양한 메뉴 화면과 메뉴 항목 선택 처리를 담당합니다.
"""

import sys
from functools import lru_cache

from modules.utils import clear_screen, format_time, format_datetime

class MenuManager:
    """메뉴 관리 클래스"""
    
    def __init__(self, app):
        """메뉴 관리자 초기화
        
        Args:
            app: 메인 애플리케이션 인스턴스 (의존성 주입)
        """
        self.app = app
        self.ui_manager = None  # UI 매니저는 나중에 설정됨
        
    def set_ui_manager(self, ui_manager):
        """UI 매니저 설정 (순환 참조 방지)
        
        Args:
            ui_manager: UI 매니저 인스턴스
        """
        self.ui_manager = ui_manager
    
    def display_menu_header(self, title):
        """메뉴 헤더 표시
        
        Args:
            title (str): 메뉴 제목
        """
        clear_screen()
        print("\n" + "=" * 50)
        print(f"{title:^50}")
        print("=" * 50 + "\n")
        
    @staticmethod
    def get_user_input(prompt="선택하세요: "):
        """사용자 입력 받기
        
        Args:
            prompt (str): 입력 프롬프트 메시지
            
        Returns:
            str: 사용자 입력 문자열
        """
        return input(prompt).strip()
        
    @staticmethod
    def show_message_and_wait(message="잘못된 선택입니다."):
        """메시지를 표시하고 사용자 입력을 기다림
        
        Args:
            message (str): 표시할 메시지
        """
        print(f"\n{message}")
        input("계속하려면 Enter 키를 누르세요...")
        
    def select_item_from_menu(self, items, prompt="선택하세요 (번호): ", empty_message="항목이 없습니다.", back_menu_name="이전 메뉴"):
        """메뉴에서 항목 선택
        
        Args:
            items (list): 메뉴 항목 리스트
            prompt (str): 선택 프롬프트 메시지
            empty_message (str): 항목이 없을 때 표시할 메시지
            back_menu_name (str): 뒤로 가기 메뉴 이름
            
        Returns:
            tuple: (선택된 항목의 인덱스, 선택된 항목) 또는 (-1, None) 뒤로 가기 선택 시
        """
        if not items:
            print(f"\n{empty_message}")
            self.show_message_and_wait()
            return -1, None
            
        for i, item in enumerate(items, 1):
            print(f"{i}. {item}")
            
        print(f"0. {back_menu_name}")
        
        while True:
            try:
                choice = int(self.get_user_input(prompt))
                
                if choice == 0:
                    return -1, None
                elif 1 <= choice <= len(items):
                    return choice - 1, items[choice - 1]
                else:
                    print("잘못된 선택입니다. 다시 선택해주세요.")
            except ValueError:
                print("숫자를 입력해주세요.")
                
    def format_product_info(self, product, include_index=False, index=None):
        """제품 정보 형식화
        
        Args:
            product: 제품 객체
            include_index (bool): 인덱스 포함 여부
            index (int, optional): 표시할 인덱스
            
        Returns:
            str: 형식화된 제품 정보 문자열
        """
        cooking_time = format_time(product.cooking_time)
        
        if include_index:
            return f"{index}. {product.name} ({product.category}) - {cooking_time} {'★' if product.favorite else ''}"
        else:
            return f"{product.name} ({product.category}) - {cooking_time} {'★' if product.favorite else ''}"
            
    @staticmethod
    @lru_cache(maxsize=32)
    def format_product_detail(product):
        """제품 상세 정보 형식화
        
        Args:
            product: 제품 객체
            
        Returns:
            str: 형식화된 제품 상세 정보 문자열
        """
        result = []
        result.append(f"이름: {product.name}")
        result.append(f"카테고리: {product.category}")
        result.append(f"조리 시간: {format_time(product.cooking_time)}")
        
        if product.description:
            result.append(f"설명: {product.description}")
            
        result.append(f"즐겨찾기: {'예' if product.favorite else '아니오'}")
        
        last_used = format_datetime(product.last_used) if product.last_used else "없음"
        result.append(f"마지막 사용: {last_used}")
        
        if product.instructions:
            result.append("\n[조리 방법]")
            for i, instruction in enumerate(product.instructions, 1):
                result.append(f"{i}. {instruction}")
                
        return "\n".join(result) 