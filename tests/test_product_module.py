"""
Product 모듈 단위 테스트

이 모듈은 modules/product_module.py의 기능을 테스트합니다.
주요 테스트 대상:
1. Product 클래스의 기능
2. ProductManager 클래스의 CRUD 기능
3. 예외 처리 및 에러 케이스
"""

import unittest
import os
import tempfile
import datetime
from pathlib import Path
import sys

# 상위 디렉토리를 임포트 경로에 추가 (상대 경로 임포트를 위함)
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.product_module import (
    Product, 
    ProductManager, 
    ProductNotFoundError,
    ProductValidationError,
    ProductDuplicateError,
    ProductDataError
)


class TestProduct(unittest.TestCase):
    """Product 클래스 단위 테스트"""
    
    def test_product_init_with_required_fields(self):
        """필수 필드만으로 Product 객체가 생성되는지 테스트"""
        product = Product(
            name={"ko": "테스트 제품"}
        )
        
        self.assertIsNotNone(product.id)  # 자동 생성된 ID 확인
        self.assertEqual("테스트 제품", product.get_localized_name())
        self.assertEqual("", product.category)
        self.assertEqual(0, product.cook_time)
        
    def test_product_init_missing_required_field(self):
        """필수 필드 누락 시 예외가 발생하는지 테스트"""
        with self.assertRaises(ProductValidationError):
            Product(name=None)
            
    def test_product_validation(self):
        """유효성 검증이 올바르게 작동하는지 테스트"""
        # 유효한 제품
        product = Product(
            name={"ko": "테스트 제품"}
        )
        self.assertTrue(product.validate())
        
        # 유효하지 않은 제품 (name 필드 비어있음)
        product.name = {}
        with self.assertRaises(ProductValidationError) as cm:
            product.validate()
        self.assertIn("name", cm.exception.invalid_fields)
        
        # 유효하지 않은 제품 (cook_time 음수)
        product.name = {"ko": "테스트 제품"}
        product.cook_time = -1
        with self.assertRaises(ProductValidationError) as cm:
            product.validate()
        self.assertIn("cook_time", cm.exception.invalid_fields)
        
    def test_localized_name_and_description(self):
        """다국어 처리가 올바르게 작동하는지 테스트"""
        product = Product(
            name={"ko": "한국어 이름", "en": "English Name"},
            description={"ko": "한국어 설명", "en": "English Description"}
        )
        
        # 기본 언어 테스트
        self.assertEqual("한국어 이름", product.get_localized_name())
        self.assertEqual("한국어 설명", product.get_localized_description())
        
        # 지정된 언어 테스트
        self.assertEqual("English Name", product.get_localized_name("en"))
        self.assertEqual("English Description", product.get_localized_description("en"))
        
        # 존재하지 않는 언어 테스트 (첫 번째 항목 반환)
        self.assertEqual("한국어 이름", product.get_localized_name("fr"))
        self.assertEqual("한국어 설명", product.get_localized_description("fr"))
        
    def test_to_dict_and_from_dict(self):
        """to_dict 및 from_dict 메서드가 올바르게 작동하는지 테스트"""
        # 원본 제품 생성
        original = Product(
            id="test-id",
            name={"ko": "테스트 제품", "en": "Test Product"},
            description={"ko": "테스트 설명", "en": "Test Description"},
            category="테스트 카테고리",
            cook_time=180,
            manufacturer="테스트 제조사",
            tags=["test", "product"],
            favorite=True,
            last_used=datetime.datetime.now(),
            nutrition={"calories": 350},
            ingredients=["재료1", "재료2"],
            cooking_steps=[{"step": 1, "description": "물을 넣는다"}],
            custom_data={"custom_key": "custom_value"}
        )
        
        # 딕셔너리로 변환
        data_dict = original.to_dict()
        
        # 딕셔너리에서 다시 객체로 변환
        restored = Product.from_dict(data_dict)
        
        # 원본과 복원된 객체 비교
        self.assertEqual(original.id, restored.id)
        self.assertEqual(original.name, restored.name)
        self.assertEqual(original.description, restored.description)
        self.assertEqual(original.category, restored.category)
        self.assertEqual(original.cook_time, restored.cook_time)
        self.assertEqual(original.manufacturer, restored.manufacturer)
        self.assertEqual(original.tags, restored.tags)
        self.assertEqual(original.favorite, restored.favorite)
        self.assertEqual(original.nutrition, restored.nutrition)
        self.assertEqual(original.ingredients, restored.ingredients)
        self.assertEqual(original.cooking_steps, restored.cooking_steps)
        self.assertEqual(original.custom_data, restored.custom_data)
        
    def test_search_keywords(self):
        """검색 키워드 생성이 올바르게 작동하는지 테스트"""
        product = Product(
            name={"ko": "테스트 제품", "en": "Test Product"},
            description={"ko": "테스트 설명", "en": "Test Description"},
            category="테스트 카테고리",
            manufacturer="테스트 제조사",
            tags=["tag1", "tag2"]
        )
        
        keywords = product.get_search_keywords()
        
        # 중요 키워드 포함 검사
        self.assertIn("테스트 제품", keywords)
        self.assertIn("test product", keywords)
        self.assertIn("테스트 설명", keywords)
        self.assertIn("test description", keywords)
        self.assertIn("테스트 카테고리", keywords)
        self.assertIn("테스트 제조사", keywords)
        self.assertIn("tag1", keywords)
        self.assertIn("tag2", keywords)
        
        # 캐싱 확인
        self.assertIsNotNone(product._search_keywords)
        
        # 두 번째 호출은 캐시된 값 사용
        cached_keywords = product.get_search_keywords()
        self.assertIs(keywords, cached_keywords)


class TestProductManager(unittest.TestCase):
    """ProductManager 클래스 단위 테스트"""
    
    def setUp(self):
        """각 테스트 전에 실행되는 설정"""
        # 테스트용 임시 파일 경로 생성
        self.temp_dir = tempfile.gettempdir()
        self.test_data_path = os.path.join(self.temp_dir, f"test_products_{datetime.datetime.now().timestamp()}.json")
        
        # 테스트용 ProductManager 인스턴스 생성
        self.manager = ProductManager.create_test_instance(self.test_data_path)
        self.manager.reset_for_test()
        
    def tearDown(self):
        """각 테스트 후에 실행되는 정리"""
        self.manager.reset_for_test()
        # 임시 파일이 남아있으면 삭제
        if os.path.exists(self.test_data_path):
            try:
                os.remove(self.test_data_path)
            except:
                pass
        
    def test_add_product(self):
        """제품 추가 기능이 올바르게 작동하는지 테스트"""
        # 테스트 제품 생성
        product = ProductManager.create_test_product()
        
        # 제품 추가
        self.manager.add_product(product)
        
        # 추가된 제품 확인
        products = self.manager.get_all_products()
        self.assertEqual(1, len(products))
        self.assertEqual(product.id, products[0].id)
        
        # get_product_by_id로 확인
        retrieved = self.manager.get_product_by_id(product.id)
        self.assertEqual(product.id, retrieved.id)
        self.assertEqual(product.name, retrieved.name)
        
    def test_add_duplicate_product(self):
        """중복 제품 추가 시 예외가 발생하는지 테스트"""
        # 테스트 제품 생성 및 추가
        product = ProductManager.create_test_product()
        self.manager.add_product(product)
        
        # 동일한 ID로 다른 제품 추가 시도
        duplicate = Product(
            id=product.id,  # 동일한 ID
            name={"ko": "중복 제품"}
        )
        
        # 예외 발생 확인
        with self.assertRaises(ProductDuplicateError) as cm:
            self.manager.add_product(duplicate)
        self.assertEqual(product.id, cm.exception.product_id)
        
    def test_update_product(self):
        """제품 업데이트 기능이 올바르게 작동하는지 테스트"""
        # 테스트 제품 추가
        product = ProductManager.create_test_product()
        self.manager.add_product(product)
        
        # 업데이트할 데이터
        updated_data = {
            "name": {"ko": "업데이트된 이름", "en": "Updated Name"},
            "cook_time": 300,
            "favorite": True
        }
        
        # 제품 업데이트
        self.manager.update_product(product.id, updated_data)
        
        # 업데이트된 제품 확인
        updated = self.manager.get_product_by_id(product.id)
        self.assertEqual(updated_data["name"], updated.name)
        self.assertEqual(updated_data["cook_time"], updated.cook_time)
        self.assertEqual(updated_data["favorite"], updated.favorite)
        
    def test_update_nonexistent_product(self):
        """존재하지 않는 제품 업데이트 시 예외가 발생하는지 테스트"""
        with self.assertRaises(ProductNotFoundError) as cm:
            self.manager.update_product("nonexistent-id", {"name": {"ko": "새 이름"}})
        self.assertEqual("nonexistent-id", cm.exception.product_id)
        
    def test_delete_product(self):
        """제품 삭제 기능이 올바르게 작동하는지 테스트"""
        # 테스트 제품 추가
        product = ProductManager.create_test_product()
        self.manager.add_product(product)
        
        # 제품이 추가되었는지 확인
        self.assertEqual(1, len(self.manager.get_all_products()))
        
        # 제품 삭제
        self.manager.delete_product(product.id)
        
        # 제품이 삭제되었는지 확인
        self.assertEqual(0, len(self.manager.get_all_products()))
        self.assertIsNone(self.manager.get_product_by_id(product.id))
        
    def test_delete_nonexistent_product(self):
        """존재하지 않는 제품 삭제 시 예외가 발생하는지 테스트"""
        with self.assertRaises(ProductNotFoundError) as cm:
            self.manager.delete_product("nonexistent-id")
        self.assertEqual("nonexistent-id", cm.exception.product_id)
        
    def test_get_products_by_category(self):
        """카테고리별 제품 조회 기능이 올바르게 작동하는지 테스트"""
        # 다양한 카테고리의 테스트 제품 추가
        self.manager.add_test_products(6)  # 각 카테고리별 2개씩 추가됨
        
        # 카테고리별 제품 조회
        category = "테스트라면"
        products = self.manager.get_products_by_category(category)
        
        # 조회된 제품 확인
        self.assertEqual(2, len(products))
        for product in products:
            self.assertEqual(category, product.category)
            
    def test_get_favorite_products(self):
        """즐겨찾기 제품 조회 기능이 올바르게 작동하는지 테스트"""
        # 테스트 제품 추가 (짝수 번호는 즐겨찾기로 설정됨)
        self.manager.add_test_products(5)
        
        # 즐겨찾기 제품 조회
        favorites = self.manager.get_favorite_products()
        
        # 조회된 제품 확인 (3개 예상: 0, 2, 4번 인덱스)
        self.assertEqual(3, len(favorites))
        for product in favorites:
            self.assertTrue(product.favorite)
            
    def test_search_products(self):
        """제품 검색 기능이 올바르게 작동하는지 테스트"""
        # 테스트 제품 추가
        self.manager.add_test_products(5)
        
        # 검색어로 검색
        results = self.manager.search_products("테스트")
        
        # 모든 제품이 검색되는지 확인
        self.assertEqual(5, len(results))
        
        # 특정 제품 검색
        results = self.manager.search_products("테스트 제품 1")
        self.assertEqual(1, len(results))
        self.assertEqual("테스트 제품 1", results[0].get_localized_name())
        
        # 태그로 검색
        results = self.manager.search_products("tag1")
        self.assertEqual(1, len(results))
        
    def test_save_and_load_products(self):
        """제품 저장 및 로드 기능이 올바르게 작동하는지 테스트"""
        # 테스트 제품 추가
        original_products = self.manager.add_test_products(3)
        
        # 제품 저장
        self.manager.save_products()
        
        # 저장된 파일이 있는지 확인
        self.assertTrue(os.path.exists(self.test_data_path))
        
        # 데이터를 초기화하고 다시 로드
        self.manager.reset_for_test()
        self.manager.data_path = self.test_data_path  # 경로 재설정
        self.manager.load_products()
        
        # 로드된 제품 확인
        loaded_products = self.manager.get_all_products()
        self.assertEqual(len(original_products), len(loaded_products))
        
        # 원본 제품과 로드된 제품 비교
        for orig in original_products:
            loaded = self.manager.get_product_by_id(orig.id)
            self.assertIsNotNone(loaded)
            self.assertEqual(orig.name, loaded.name)
            self.assertEqual(orig.category, loaded.category)
            self.assertEqual(orig.cook_time, loaded.cook_time)


if __name__ == '__main__':
    unittest.main() 