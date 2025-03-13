#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
한국 간편식품 제품 데이터를 관리하는 모듈

이 모듈은 K-Food Timer 앱에서 사용하는 한국 간편식품 제품 정보를 관리합니다.
Product 클래스와 ProductManager 클래스를 제공하여 제품 데이터의 CRUD 작업을 지원합니다.
"""

import os
import json
import uuid
import logging
import datetime
from typing import Dict, List, Optional, Any, Union

# 로깅 설정
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

class Product:
    """제품 정보 클래스
    
    식품의 이름, 카테고리, 조리 시간, 조리 안내 등의 정보를 관리합니다.
    """
    
    def __init__(
        self,
        name: Union[str, Dict[str, str]],
        category: str,
        cooking_time: int,
        manufacturer: str = "",
        description: Union[str, Dict[str, str]] = "",
        image_url: str = "",
        barcode: str = "",
        instructions: List[Union[str, Dict[str, str]]] = None,
        id: str = None,
        favorite: bool = False,
        featured: bool = False,
        tags: List[str] = None,
        last_used: str = None
    ):
        """Product 초기화
        
        Args:
            name (Union[str, Dict[str, str]]): 제품 이름 (단일 문자열 또는 {'ko': '한국어 이름', 'en': '영어 이름'} 형식)
            category (str): 제품 카테고리
            cooking_time (int): 조리 시간(초)
            manufacturer (str, optional): 제조사
            description (Union[str, Dict[str, str]], optional): 제품 설명
            image_url (str, optional): 제품 이미지 URL
            barcode (str, optional): 제품 바코드
            instructions (List[Union[str, Dict[str, str]]], optional): 조리 안내 단계
            id (str, optional): 제품 고유 ID (없으면 자동 생성)
            favorite (bool, optional): 즐겨찾기 여부
            featured (bool, optional): 특집 제품 여부
            tags (List[str], optional): 제품 태그 목록
            last_used (str, optional): 마지막 사용 시간 (ISO 포맷)
        """
        self.id = id if id else str(uuid.uuid4())
        self.name = name
        self.category = category
        self.cooking_time = cooking_time
        self.manufacturer = manufacturer
        self.description = description
        self.image_url = image_url
        self.barcode = barcode
        self.instructions = instructions if instructions else []
        self.favorite = favorite
        self.featured = featured
        self.tags = tags if tags else []
        self.last_used = last_used
        
    def __str__(self) -> str:
        """제품 객체의 문자열 표현
        
        Returns:
            str: 제품 정보 문자열
        """
        name = self.get_localized_name()
        return f"{name} ({self.category}, {self.cooking_time}초)"
        
    def validate(self) -> None:
        """제품 정보 검증
        
        필수 필드와 타입을 검사합니다.
        
        Raises:
            ValueError: 검증 실패 시 발생
        """
        # 필수 필드 검사
        if not self.name:
            raise ValueError("제품 이름은 필수입니다.")
        if not self.category:
            raise ValueError("카테고리는 필수입니다.")
        if not self.cooking_time or self.cooking_time <= 0:
            raise ValueError("유효한 조리 시간이 필요합니다.")
            
        # 타입 검사
        if not isinstance(self.name, (str, dict)):
            raise ValueError("이름은 문자열 또는 딕셔너리여야 합니다.")
        if not isinstance(self.cooking_time, int):
            raise ValueError("조리 시간은 정수(초)여야 합니다.")
        if not isinstance(self.instructions, list):
            raise ValueError("조리 안내는 리스트여야 합니다.")
        if not isinstance(self.tags, list):
            raise ValueError("태그는 리스트여야 합니다.")
            
    def get_localized_name(self, lang: str = "ko") -> str:
        """지역화된 이름 조회
        
        Args:
            lang (str, optional): 언어 코드 (기본값: "ko")
            
        Returns:
            str: 지역화된 이름 또는 기본 이름
        """
        if isinstance(self.name, dict):
            return self.name.get(lang, next(iter(self.name.values()), ""))
        return self.name
        
    def get_localized_description(self, lang: str = "ko") -> str:
        """지역화된 설명 조회
        
        Args:
            lang (str, optional): 언어 코드 (기본값: "ko")
            
        Returns:
            str: 지역화된 설명 또는 기본 설명
        """
        if isinstance(self.description, dict):
            return self.description.get(lang, next(iter(self.description.values()), ""))
        return self.description
        
    def get_localized_instruction(self, step: int, lang: str = "ko") -> str:
        """지역화된 조리 안내 단계 조회
        
        Args:
            step (int): 조리 단계 인덱스
            lang (str, optional): 언어 코드 (기본값: "ko")
            
        Returns:
            str: 지역화된 조리 안내 또는 기본 안내
        """
        if step < 0 or step >= len(self.instructions):
            return ""
            
        instruction = self.instructions[step]
        if isinstance(instruction, dict):
            return instruction.get(lang, next(iter(instruction.values()), ""))
        return instruction
        
    def toggle_favorite(self) -> bool:
        """즐겨찾기 상태 전환
        
        Returns:
            bool: 변경된 즐겨찾기 상태
        """
        self.favorite = not self.favorite
        return self.favorite
        
    def update_last_used(self) -> None:
        """마지막 사용 시간 업데이트"""
        self.last_used = datetime.datetime.now().isoformat()
        
    def to_dict(self) -> Dict[str, Any]:
        """제품 정보를 딕셔너리로 변환
        
        Returns:
            dict: 제품 정보 딕셔너리
        """
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "cooking_time": self.cooking_time,
            "manufacturer": self.manufacturer,
            "description": self.description,
            "image_url": self.image_url,
            "barcode": self.barcode,
            "instructions": self.instructions,
            "favorite": self.favorite,
            "featured": self.featured,
            "tags": self.tags,
            "last_used": self.last_used
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """딕셔너리에서 제품 객체 생성
        
        Args:
            data (dict): 제품 정보 딕셔너리
            
        Returns:
            Product: 생성된 제품 객체
        """
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            category=data.get("category", ""),
            cooking_time=data.get("cooking_time", 0),
            manufacturer=data.get("manufacturer", ""),
            description=data.get("description", ""),
            image_url=data.get("image_url", ""),
            barcode=data.get("barcode", ""),
            instructions=data.get("instructions", []),
            favorite=data.get("favorite", False),
            featured=data.get("featured", False),
            tags=data.get("tags", []),
            last_used=data.get("last_used")
        )


class ProductManager:
    """제품 관리 클래스
    
    제품 데이터의 로드, 저장, 검색, 필터링, 추가, 수정 등의 기능을 제공합니다.
    """
    
    def __init__(self, data_path: str = "data/products.json"):
        """ProductManager 초기화
        
        Args:
            data_path (str): 제품 데이터 파일 경로
        """
        self.data_path = data_path
        self.products = []  # Product 객체 리스트
        self._ensure_data_dir()
        
    def _ensure_data_dir(self) -> None:
        """데이터 디렉토리 존재 확인 및 생성"""
        data_dir = os.path.dirname(self.data_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            logger.info(f"데이터 디렉토리 생성: {data_dir}")
            
    def load_products(self) -> bool:
        """제품 데이터 로드
        
        JSON 파일에서 제품 데이터를 읽어 products 리스트에 Product 객체로 저장합니다.
        
        Returns:
            bool: 로드 성공 여부
        """
        if not os.path.exists(self.data_path):
            logger.warning(f"제품 데이터 파일이 없습니다: {self.data_path}")
            # 초기 제품 데이터 생성
            self._create_default_products()
            return True
            
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.products = [Product.from_dict(product_data) for product_data in data]
            logger.info(f"{len(self.products)}개의 제품 데이터를 로드했습니다.")
            return True
        except Exception as e:
            logger.error(f"제품 데이터 로드 중 오류 발생: {e}")
            # 파일 손상 시 초기 데이터 생성
            self._create_default_products()
            return False
    
    def save_products(self) -> bool:
        """제품 데이터 저장
        
        products 리스트의 Product 객체를 JSON 형식으로 파일에 저장합니다.
        
        Returns:
            bool: 저장 성공 여부
        """
        try:
            data = [product.to_dict() for product in self.products]
            
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"{len(self.products)}개의 제품 데이터를 저장했습니다.")
            return True
        except Exception as e:
            logger.error(f"제품 데이터 저장 중 오류 발생: {e}")
            return False
    
    def get_all_products(self) -> List[Product]:
        """모든 제품 조회
        
        Returns:
            list: 모든 Product 객체 리스트
        """
        return self.products
        
    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """ID로 제품 조회
        
        Args:
            product_id (str): 조회할 제품 ID
            
        Returns:
            Product: 찾은 Product 객체 또는 None
        """
        for product in self.products:
            if product.id == product_id:
                return product
        return None
        
    def get_products_by_category(self, category: str) -> List[Product]:
        """카테고리로 제품 필터링
        
        Args:
            category (str): 필터링할 카테고리
            
        Returns:
            list: 필터링된 Product 객체 리스트
        """
        return [product for product in self.products if product.category == category]
        
    def get_favorite_products(self) -> List[Product]:
        """즐겨찾기 제품 조회
        
        Returns:
            list: 즐겨찾기된 Product 객체 리스트
        """
        return [product for product in self.products if product.favorite]
        
    def get_recent_products(self, limit: int = 5) -> List[Product]:
        """최근 사용한 제품 조회
        
        Args:
            limit (int): 최대 개수
            
        Returns:
            list: 최근 사용한 순으로 정렬된 Product 객체 리스트
        """
        # last_used가 있는 제품만 필터링하고 날짜 기준으로 내림차순 정렬
        used_products = [p for p in self.products if p.last_used]
        used_products.sort(key=lambda p: p.last_used, reverse=True)
        return used_products[:limit]
        
    def get_categories(self) -> List[str]:
        """모든 카테고리 조회
        
        Returns:
            list: 카테고리 문자열 리스트 (중복 제거, 정렬됨)
        """
        categories = set(product.category for product in self.products)
        return sorted(list(categories))
        
    def add_product(self, product: Product) -> bool:
        """새 제품 추가
        
        Args:
            product (Product): 추가할 Product 객체
            
        Returns:
            bool: 추가 성공 여부
        """
        # ID 중복 검사
        if self.get_product_by_id(product.id):
            logger.warning(f"이미 존재하는 제품 ID입니다: {product.id}")
            return False
            
        try:
            # 제품 정보 검증
            product.validate()
            
            # 제품 추가
            self.products.append(product)
            logger.info(f"새 제품이 추가되었습니다: {product.id} ({product.get_localized_name()})")
            return True
        except ValueError as e:
            logger.error(f"제품 추가 실패: {e}")
            return False
            
    def update_product(self, product_id: str, updated_data: Dict[str, Any]) -> bool:
        """제품 정보 업데이트
        
        Args:
            product_id (str): 업데이트할 제품 ID
            updated_data (dict): 업데이트할 데이터
            
        Returns:
            bool: 업데이트 성공 여부
        """
        product = self.get_product_by_id(product_id)
        if not product:
            logger.warning(f"존재하지 않는 제품 ID입니다: {product_id}")
            return False
            
        try:
            # 업데이트할 속성만 변경
            for key, value in updated_data.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            
            # 제품 정보 검증
            product.validate()
            
            logger.info(f"제품 정보가 업데이트되었습니다: {product_id}")
            return True
        except (ValueError, AttributeError) as e:
            logger.error(f"제품 업데이트 실패: {e}")
            return False
            
    def delete_product(self, product_id: str) -> bool:
        """제품 삭제
        
        Args:
            product_id (str): 삭제할 제품 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        product = self.get_product_by_id(product_id)
        if not product:
            logger.warning(f"존재하지 않는 제품 ID입니다: {product_id}")
            return False
            
        self.products.remove(product)
        logger.info(f"제품이 삭제되었습니다: {product_id}")
        return True
        
    def search_products(self, query: str) -> List[Product]:
        """제품 검색
        
        제품 이름, 설명, 제조사, 태그 등에서 검색어를 포함하는 제품을 찾습니다.
        
        Args:
            query (str): 검색어
            
        Returns:
            list: 검색 결과 Product 객체 리스트
        """
        query = query.lower()
        results = []
        
        for product in self.products:
            # 이름 검색
            name = product.get_localized_name()
            if isinstance(product.name, dict):
                for lang_name in product.name.values():
                    if query in lang_name.lower():
                        results.append(product)
                        break
            elif query in name.lower():
                results.append(product)
                continue
                
            # 설명 검색
            description = product.get_localized_description()
            if isinstance(product.description, dict):
                for lang_desc in product.description.values():
                    if query in lang_desc.lower():
                        results.append(product)
                        break
            elif query in description.lower():
                results.append(product)
                continue
                
            # 제조사 검색
            if query in product.manufacturer.lower():
                results.append(product)
                continue
                
            # 태그 검색
            for tag in product.tags:
                if query in tag.lower():
                    results.append(product)
                    break
                    
        return results
    
    def _create_default_products(self) -> None:
        """기본 제품 데이터 생성
        
        초기 실행 시 또는 데이터 파일 손상 시 사용됩니다.
        """
        # 라면류
        ramen_products = [
            Product(
                name={"ko": "신라면", "en": "Shin Ramyun"},
                category="라면류",
                cooking_time=180,  # 3분
                manufacturer="농심",
                description={"ko": "매운맛이 특징인 대표적인 한국 라면", "en": "Spicy Korean instant noodle"},
                image_url="https://example.com/images/shin_ramyun.jpg",
                barcode="8801043012072",
                instructions=[
                    {"ko": "물 550ml를 냄비에 넣고 끓인다", "en": "Boil 550ml of water in a pot"},
                    {"ko": "면과 스프를 넣는다", "en": "Add noodles and soup powder"},
                    {"ko": "3분간 더 끓인다", "en": "Boil for 3 more minutes"},
                    {"ko": "불을 끄고 그릇에 담아 먹는다", "en": "Turn off heat and serve"}
                ],
                featured=True,
                tags=["매운맛", "인기", "국민라면"]
            ),
            Product(
                name={"ko": "진라면 매운맛", "en": "Jin Ramen Spicy"},
                category="라면류",
                cooking_time=180,  # 3분
                manufacturer="오뚜기",
                description={"ko": "진한 맛이 특징인 매운 라면", "en": "Rich and spicy Korean instant noodle"},
                image_url="https://example.com/images/jin_ramen_spicy.jpg",
                barcode="8801045321219",
                instructions=[
                    {"ko": "물 550ml를 냄비에 넣고 끓인다", "en": "Boil 550ml of water in a pot"},
                    {"ko": "면과 스프를 넣는다", "en": "Add noodles and soup powder"},
                    {"ko": "3분간 더 끓인다", "en": "Boil for 3 more minutes"},
                    {"ko": "불을 끄고 그릇에 담아 먹는다", "en": "Turn off heat and serve"}
                ],
                tags=["매운맛", "진한맛"]
            ),
            Product(
                name={"ko": "진라면 순한맛", "en": "Jin Ramen Mild"},
                category="라면류",
                cooking_time=180,  # 3분
                manufacturer="오뚜기",
                description={"ko": "부드러운 국물맛이 특징인 순한 라면", "en": "Mild flavored Korean instant noodle"},
                image_url="https://example.com/images/jin_ramen_mild.jpg",
                barcode="8801045321226",
                instructions=[
                    {"ko": "물 550ml를 냄비에 넣고 끓인다", "en": "Boil 550ml of water in a pot"},
                    {"ko": "면과 스프를 넣는다", "en": "Add noodles and soup powder"},
                    {"ko": "3분간 더 끓인다", "en": "Boil for 3 more minutes"},
                    {"ko": "불을 끄고 그릇에 담아 먹는다", "en": "Turn off heat and serve"}
                ],
                tags=["순한맛", "국물라면"]
            ),
            Product(
                name={"ko": "삼양라면", "en": "Samyang Ramen"},
                category="라면류",
                cooking_time=210,  # 3분 30초
                manufacturer="삼양식품",
                description={"ko": "국민 라면 중 하나로 얼큰한 맛이 특징", "en": "One of Korea's classic spicy instant noodles"},
                image_url="https://example.com/images/samyang_ramen.jpg",
                barcode="8801073101012",
                instructions=[
                    {"ko": "물 550ml를 냄비에 넣고 끓인다", "en": "Boil 550ml of water in a pot"},
                    {"ko": "면과 스프를 넣는다", "en": "Add noodles and soup powder"},
                    {"ko": "3분 30초간 더 끓인다", "en": "Boil for 3 minutes and 30 seconds more"},
                    {"ko": "불을 끄고 그릇에 담아 먹는다", "en": "Turn off heat and serve"}
                ],
                tags=["매운맛", "전통라면"]
            ),
            Product(
                name={"ko": "불닭볶음면", "en": "Buldak Hot Chicken Ramen"},
                category="라면류",
                cooking_time=150,  # 2분 30초
                manufacturer="삼양식품",
                description={"ko": "매우 매운 맛이 특징인 볶음면", "en": "Extremely spicy stir-fried noodles"},
                image_url="https://example.com/images/buldak.jpg",
                barcode="8801073141162",
                instructions=[
                    {"ko": "물 600ml를 냄비에 넣고 끓인다", "en": "Boil 600ml of water in a pot"},
                    {"ko": "면을 넣고 2분 30초간 삶는다", "en": "Add noodles and boil for 2 minutes and 30 seconds"},
                    {"ko": "물을 버리고 액상스프와 후레이크를 넣는다", "en": "Drain water and add liquid sauce and flakes"},
                    {"ko": "잘 섞어서 먹는다", "en": "Mix well and serve"}
                ],
                featured=True,
                tags=["매운맛", "볶음면", "극한매운맛", "챌린지"]
            ),
            Product(
                name={"ko": "짜파게티", "en": "Chapagetti"},
                category="라면류",
                cooking_time=240,  # 4분
                manufacturer="농심",
                description={"ko": "짜장맛 라면의 대표주자", "en": "Popular Korean black bean sauce instant noodles"},
                image_url="https://example.com/images/chapagetti.jpg",
                barcode="8801043015042",
                instructions=[
                    {"ko": "물 550ml를 냄비에 넣고 끓인다", "en": "Boil 550ml of water in a pot"},
                    {"ko": "면과 건더기스프를 넣고 4분간 삶는다", "en": "Add noodles and vegetable flakes and boil for 4 minutes"},
                    {"ko": "물을 80ml만 남기고 버린다", "en": "Drain water leaving only 80ml"},
                    {"ko": "분말스프와 기름을 넣고 잘 비빈다", "en": "Add powder soup and oil and mix well"}
                ],
                tags=["짜장맛", "볶음면"]
            ),
        ]
        
        # 떡볶이류
        tteokbokki_products = [
            Product(
                name={"ko": "신당동 떡볶이", "en": "Sindangdong Tteokbokki"},
                category="떡볶이류",
                cooking_time=300,  # 5분
                manufacturer="CJ제일제당",
                description={"ko": "서울 신당동 즉석 떡볶이 맛을 재현한 제품", "en": "Instant tteokbokki inspired by Seoul's Sindangdong district"},
                image_url="https://example.com/images/sindangdong_tteokbokki.jpg",
                barcode="8801097342118",
                instructions=[
                    {"ko": "물 300ml를 냄비에 넣고 소스를 부어 끓인다", "en": "Pour 300ml of water into a pot and add the sauce"},
                    {"ko": "끓으면 떡과 어묵을 넣고 5분간 끓인다", "en": "Once boiling, add rice cakes and fish cakes and boil for 5 minutes"},
                    {"ko": "물이 졸아들면 불을 끄고 뚜껑을 덮어 2분간 뜸을 들인다", "en": "When water reduces, turn off heat and cover for 2 minutes"}
                ],
                featured=True,
                tags=["매운맛", "국민간식", "분식"]
            ),
            Product(
                name={"ko": "컵 떡볶이", "en": "Cup Tteokbokki"},
                category="떡볶이류",
                cooking_time=240,  # 4분
                manufacturer="오뚜기",
                description={"ko": "간편하게 즐기는 컵 떡볶이", "en": "Convenient cup-type tteokbokki"},
                image_url="https://example.com/images/cup_tteokbokki.jpg",
                barcode="8801045857121",
                instructions=[
                    {"ko": "뚜껑을 반만 열고 소스를 뿌린다", "en": "Open lid halfway and pour the sauce"},
                    {"ko": "뜨거운 물을 표시선까지 붓는다", "en": "Pour hot water up to the line"},
                    {"ko": "뚜껑을 덮고 4분간 기다린다", "en": "Cover and wait for 4 minutes"},
                    {"ko": "잘 저어서 먹는다", "en": "Stir well and serve"}
                ],
                tags=["간편식", "컵제품", "매운맛"]
            ),
            Product(
                name={"ko": "라볶이", "en": "Rabokki"},
                category="떡볶이류",
                cooking_time=270,  # 4분 30초
                manufacturer="농심",
                description={"ko": "라면과 떡볶이의 맛을 함께 즐기는 제품", "en": "A combination of ramen and tteokbokki"},
                image_url="https://example.com/images/rabokki.jpg",
                barcode="8801043015677",
                instructions=[
                    {"ko": "물 500ml를 냄비에 넣고 끓인다", "en": "Boil 500ml of water in a pot"},
                    {"ko": "끓으면 면과 떡, 스프를 넣는다", "en": "Once boiling, add noodles, rice cakes, and soup powder"},
                    {"ko": "4분 30초간 끓인다", "en": "Boil for 4 minutes and 30 seconds"},
                    {"ko": "불을 끄고 잘 저어서 먹는다", "en": "Turn off heat, stir well and serve"}
                ],
                tags=["매운맛", "라면", "떡볶이", "퓨전"]
            ),
            Product(
                name={"ko": "까르보 불닭 떡볶이", "en": "Carbo Buldak Tteokbokki"},
                category="떡볶이류",
                cooking_time=300,  # 5분
                manufacturer="삼양식품",
                description={"ko": "크리미한 맛과 매운맛이 조화로운 떡볶이", "en": "Tteokbokki with a creamy and spicy flavor"},
                image_url="https://example.com/images/carbo_buldak_tteokbokki.jpg",
                barcode="8801073141292",
                instructions=[
                    {"ko": "물 300ml를 냄비에 넣고 끓인다", "en": "Boil 300ml of water in a pot"},
                    {"ko": "떡과 소스를 넣고 5분간 끓인다", "en": "Add rice cakes and sauce and boil for 5 minutes"},
                    {"ko": "물이 졸아들면 불을 약하게 하고 크림 소스를 넣는다", "en": "When water reduces, lower heat and add cream sauce"},
                    {"ko": "잘 저어서 먹는다", "en": "Stir well and serve"}
                ],
                featured=True,
                tags=["매운맛", "크림맛", "떡볶이", "퓨전"]
            ),
        ]
        
        # 만두류
        dumpling_products = [
            Product(
                name={"ko": "비비고 왕교자", "en": "Bibigo King Dumplings"},
                category="만두류",
                cooking_time=300,  # 5분
                manufacturer="CJ제일제당",
                description={"ko": "맛있는 속재료가 가득한 대형 만두", "en": "Large dumplings with delicious filling"},
                image_url="https://example.com/images/bibigo_dumplings.jpg",
                barcode="8801007356212",
                instructions=[
                    {"ko": "팬에 기름을 두른다", "en": "Oil the pan"},
                    {"ko": "만두를 넣고 중불에서 2분간 굽는다", "en": "Add dumplings and cook for 2 minutes on medium heat"},
                    {"ko": "물 1/4컵을 붓고 뚜껑을 덮는다", "en": "Pour 1/4 cup of water and cover with lid"},
                    {"ko": "3분간 더 익힌다", "en": "Cook for 3 more minutes"}
                ],
                featured=True,
                tags=["냉동식품", "만두", "간식"]
            ),
            Product(
                name={"ko": "고기 만두", "en": "Meat Dumplings"},
                category="만두류",
                cooking_time=240,  # 4분
                manufacturer="풀무원",
                description={"ko": "육즙 가득한 고기 만두", "en": "Juicy meat dumplings"},
                image_url="https://example.com/images/meat_dumplings.jpg",
                barcode="8801284123456",
                instructions=[
                    {"ko": "냄비에 물을 넣고 끓인다", "en": "Boil water in a pot"},
                    {"ko": "만두를 넣고 4분간 삶는다", "en": "Add dumplings and boil for 4 minutes"},
                    {"ko": "물을 버리고 기호에 맞게 양념한다", "en": "Drain water and season to taste"}
                ],
                tags=["냉동식품", "만두", "고기"]
            ),
            Product(
                name={"ko": "김치 만두", "en": "Kimchi Dumplings"},
                category="만두류",
                cooking_time=270,  # 4분 30초
                manufacturer="해태",
                description={"ko": "신선한 김치 맛이 일품인 만두", "en": "Dumplings with fresh kimchi flavor"},
                image_url="https://example.com/images/kimchi_dumplings.jpg",
                barcode="8801092654321",
                instructions=[
                    {"ko": "찜기에 물을 넣고 끓인다", "en": "Boil water in a steamer"},
                    {"ko": "만두를 넣고 4분 30초간 찐다", "en": "Add dumplings and steam for 4 minutes and 30 seconds"},
                    {"ko": "취향에 맞는 소스와 함께 먹는다", "en": "Serve with your preferred sauce"}
                ],
                tags=["냉동식품", "만두", "김치"]
            ),
        ]
        
        # 즉석밥/국류
        instant_rice_products = [
            Product(
                name={"ko": "햇반", "en": "Cooked White Rice"},
                category="즉석밥/국류",
                cooking_time=90,  # 1분 30초
                manufacturer="CJ제일제당",
                description={"ko": "전자레인지에 데워 먹는 즉석밥", "en": "Microwavable instant cooked rice"},
                image_url="https://example.com/images/hatban.jpg",
                barcode="8801007458342",
                instructions=[
                    {"ko": "포장의 한쪽 모서리를 1~2cm 개봉한다", "en": "Open one corner of the package 1-2cm"},
                    {"ko": "전자레인지에서 1분 30초간 가열한다", "en": "Heat in microwave for 1 minute and 30 seconds"},
                    {"ko": "그릇에 옮겨 담아 먹는다", "en": "Transfer to a bowl and serve"}
                ],
                featured=True,
                tags=["즉석밥", "간편식", "주식"]
            ),
            Product(
                name={"ko": "육개장", "en": "Yukgaejang"},
                category="즉석밥/국류",
                cooking_time=180,  # 3분
                manufacturer="오뚜기",
                description={"ko": "얼큰한 맛이 일품인 즉석 육개장", "en": "Spicy beef soup ready-to-eat"},
                image_url="https://example.com/images/yukgaejang.jpg",
                barcode="8801045721234",
                instructions=[
                    {"ko": "용기 뚜껑을 반만 열고 내용물을 섞는다", "en": "Open lid halfway and mix contents"},
                    {"ko": "뜨거운 물을 표시선까지 붓는다", "en": "Pour hot water up to the line"},
                    {"ko": "뚜껑을 덮고 3분간 기다린다", "en": "Cover and wait for 3 minutes"},
                    {"ko": "잘 저어서 먹는다", "en": "Stir well and serve"}
                ],
                tags=["즉석국", "매운맛", "한식"]
            ),
            Product(
                name={"ko": "김치찌개", "en": "Kimchi Stew"},
                category="즉석밥/국류",
                cooking_time=210,  # 3분 30초
                manufacturer="농심",
                description={"ko": "감칠맛 나는 즉석 김치찌개", "en": "Savory ready-to-eat kimchi stew"},
                image_url="https://example.com/images/kimchi_stew.jpg",
                barcode="8801043765432",
                instructions=[
                    {"ko": "용기 뚜껑을 개봉하고 건더기스프를 넣는다", "en": "Open lid and add vegetable flakes"},
                    {"ko": "뜨거운 물을 표시선까지 붓는다", "en": "Pour hot water up to the line"},
                    {"ko": "뚜껑을 덮고 3분 30초간 기다린다", "en": "Cover and wait for 3 minutes and 30 seconds"},
                    {"ko": "잘 저어서 먹는다", "en": "Stir well and serve"}
                ],
                tags=["즉석국", "김치", "한식"]
            ),
            Product(
                name={"ko": "곰탕", "en": "Beef Bone Soup"},
                category="즉석밥/국류",
                cooking_time=180,  # 3분
                manufacturer="농심",
                description={"ko": "진한 사골 맛이 일품인 즉석 곰탕", "en": "Rich beef bone soup ready-to-eat"},
                image_url="https://example.com/images/beef_bone_soup.jpg",
                barcode="8801043765433",
                instructions=[
                    {"ko": "용기 뚜껑을 개봉하고 건더기스프를 넣는다", "en": "Open lid and add vegetable flakes"},
                    {"ko": "뜨거운 물을 표시선까지 붓는다", "en": "Pour hot water up to the line"},
                    {"ko": "뚜껑을 덮고 3분간 기다린다", "en": "Cover and wait for 3 minutes"},
                    {"ko": "잘 저어서 먹는다", "en": "Stir well and serve"}
                ],
                tags=["즉석국", "곰탕", "한식", "국물요리"]
            ),
            Product(
                name={"ko": "참치마요 덮밥", "en": "Tuna Mayo Rice Bowl"},
                category="즉석밥/국류",
                cooking_time=120,  # 2분
                manufacturer="오뚜기",
                description={"ko": "참치와 마요네즈의 조합이 일품인 덮밥", "en": "Rice bowl with tuna and mayonnaise"},
                image_url="https://example.com/images/tuna_mayo_rice.jpg",
                barcode="8801045721235",
                instructions=[
                    {"ko": "용기 뚜껑을 반만 열고 소스를 넣는다", "en": "Open lid halfway and add sauce"},
                    {"ko": "전자레인지에서 2분간 가열한다", "en": "Heat in microwave for 2 minutes"},
                    {"ko": "잘 섞어서 먹는다", "en": "Mix well and serve"}
                ],
                tags=["즉석밥", "덮밥", "참치", "간편식"]
            )
        ]
        
        # 모든 제품 리스트 생성
        all_products = ramen_products + tteokbokki_products + dumpling_products + instant_rice_products
        
        # 초기 제품 데이터 저장
        self.products = all_products
        self.save_products()
        logger.info(f"{len(all_products)}개의 기본 제품 데이터를 생성했습니다.")


# 사용 예제
if __name__ == "__main__":
    # ProductManager 초기화
    manager = ProductManager()
    
    # 제품 데이터 로드
    manager.load_products()
    
    # 모든 제품 출력
    print("\n=== 모든 제품 목록 ===")
    for product in manager.get_all_products():
        print(f"- {product}")
        
    # 카테고리별 제품 출력
    print("\n=== 라면류 제품 목록 ===")
    for product in manager.get_products_by_category("라면류"):
        print(f"- {product}")
        
    # 특집 제품 출력
    print("\n=== 특집 제품 목록 ===")
    for product in manager.get_all_products():
        if product.featured:
            print(f"- {product} (특집)")
            
    # 새 제품 추가 예제
    new_product = Product(
        name={"ko": "새우탕면", "en": "Shrimp Flavored Ramen"},
        category="라면류",
        cooking_time=180,
        manufacturer="농심",
        description={"ko": "새우 맛이 일품인 라면", "en": "Ramen with delicious shrimp flavor"},
        tags=["해산물맛", "국물라면"]
    )
    
    if manager.add_product(new_product):
        print(f"\n새 제품이 추가되었습니다: {new_product}")
        
    # 제품 검색 예제
    print("\n=== '매운' 검색 결과 ===")
    for product in manager.search_products("매운"):
        print(f"- {product}")
        
    # 제품 데이터 저장
    manager.save_products() 