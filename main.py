#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K-Food Timer 애플리케이션의 메인 진입점
한국 간편식품의 조리 시간을 관리하는 타이머 앱
"""

import os
import sys
import logging
from typing import List

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 모듈 불러오기
from modules.ui_module import UI
from modules.timer_module import Timer
from modules.product_module import Product, ProductManager
from modules.settings_module import Settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KFoodTimer:
    """K-Food 타이머 앱 메인 클래스"""
    
    def __init__(self):
        """앱 초기화"""
        self.settings = Settings()
        self.product_manager = ProductManager()
        self.timer = Timer()
        self.ui = UI(self)
        
        # 데이터 로드
        self.settings.load_settings()
        self.product_manager.load_products()
        
        logger.info("앱이 초기화되었습니다.")
        
    def run(self) -> None:
        """앱 실행"""
        self.ui.main_menu()
        
    def start_product_timer(self, product_id: str) -> bool:
        """제품 타이머 시작
        
        Args:
            product_id (str): 타이머를 시작할 제품 ID
            
        Returns:
            bool: 타이머 시작 성공 여부
        """
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            logger.error(f"존재하지 않는 제품 ID: {product_id}")
            return False
            
        # 마지막 사용 시간 업데이트
        product.update_last_used()
        
        # 타이머 시작
        self.timer.start(product.cooking_time, product.get_localized_name())
        
        # 데이터 저장
        self.product_manager.save_products()
        return True
        
    def get_recent_products(self, limit: int = 5) -> List[Product]:
        """최근 사용한 제품 목록 조회
        
        Args:
            limit (int): 최대 개수
            
        Returns:
            list: 최근 사용한 Product 객체 리스트
        """
        return self.product_manager.get_recent_products(limit)
        
    def get_favorite_products(self) -> List[Product]:
        """즐겨찾기 제품 목록 조회
        
        Returns:
            list: 즐겨찾기된 Product 객체 리스트
        """
        return self.product_manager.get_favorite_products()
        
    def get_categories(self) -> List[str]:
        """카테고리 목록 조회
        
        Returns:
            list: 카테고리 문자열 리스트
        """
        return self.product_manager.get_categories()
        
    def get_products_by_category(self, category: str) -> List[Product]:
        """카테고리별 제품 목록 조회
        
        Args:
            category (str): 카테고리
            
        Returns:
            list: 해당 카테고리의 Product 객체 리스트
        """
        return self.product_manager.get_products_by_category(category)
        
    def toggle_favorite(self, product_id: str) -> bool:
        """제품 즐겨찾기 상태 전환
        
        Args:
            product_id (str): 제품 ID
            
        Returns:
            bool: 변경된 즐겨찾기 상태 또는 실패 시 None
        """
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return False
            
        status = product.toggle_favorite()
        self.product_manager.save_products()
        return status
        
    def search_products(self, query: str) -> List[Product]:
        """제품 검색
        
        Args:
            query (str): 검색어
            
        Returns:
            list: 검색 결과 Product 객체 리스트
        """
        return self.product_manager.search_products(query)
        
    def save_all_data(self) -> bool:
        """모든 데이터 저장
        
        Returns:
            bool: 저장 성공 여부
        """
        settings_saved = self.settings.save_settings()
        products_saved = self.product_manager.save_products()
        
        return settings_saved and products_saved

if __name__ == "__main__":
    app = KFoodTimer()
    try:
        app.run()
    except KeyboardInterrupt:
        app.save_all_data()
        print("\nK-Food Timer 앱을 종료합니다.")
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        app.save_all_data()
        raise 