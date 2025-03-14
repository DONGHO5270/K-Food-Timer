#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
제품 관리 모듈 (Product Management Module)

이 모듈은 K-Food Timer 애플리케이션의 제품 데이터 모델과 관리 기능을 제공합니다.

주요 구성 요소:
1. Product: 제품 데이터 모델 클래스
2. ProductDataInterface: 제품 데이터 액세스를 위한 인터페이스 클래스
3. ProductManager: 제품 데이터의 로드, 저장, 검색, 필터링 등의 기능을 수행하는 클래스
4. ProductError와 파생 예외 클래스: 제품 관련 오류 처리를 위한 예외 클래스들

사용 예시:
```python
# 제품 관리자 초기화
product_manager = ProductManager()

# 제품 데이터 로드
product_manager.load_products()

# 모든 제품 조회
products = product_manager.get_all_products()

# 특정 ID의 제품 조회
product = product_manager.get_product_by_id("ramen-001")

# 카테고리 기준 제품 필터링
ramen_products = product_manager.get_products_by_category("라면")

# 제품 검색
search_results = product_manager.search_products("신라면")

# 제품 추가
new_product = Product(id="new-product", name={"ko": "새 제품"}, category="라면", cook_time=180)
product_manager.add_product(new_product)

# 제품 정보 업데이트
product_manager.update_product("new-product", {"cook_time": 240})

# 제품 데이터 저장
product_manager.save_products()
```

참고 사항:
- 이 모듈은 JSON 파일 기반의 제품 데이터 관리를 지원합니다.
- 대용량 데이터 처리를 위한 최적화 기능을 포함하고 있습니다.
- 다국어 지원을 위한 이름 및 설명 필드의 다국어 처리가 가능합니다.
"""

import os
import json
import uuid
import logging
import datetime
import contextlib
from typing import Dict, List, Any, Optional, Union, Callable, Iterator, Generator, TypeVar, cast
from functools import lru_cache
from abc import ABC, abstractmethod

# 모듈 수준 로거 설정
logger = logging.getLogger(__name__)

# 상수 정의
DEFAULT_ENCODING = 'utf-8'
DEFAULT_JSON_INDENT = 2
MAX_LOAD_BATCH_SIZE = 1000  # 대용량 데이터 로드 시 배치 크기

# 타입 변수 정의
T = TypeVar('T')

class ProductError(Exception):
    """제품 관련 오류의 기본 예외 클래스
    
    모든 제품 관련 예외는 이 클래스를 상속받습니다.
    """
    pass
    
class ProductNotFoundError(ProductError):
    """제품을 찾을 수 없을 때 발생하는 예외
    
    Args:
        product_id: 찾을 수 없는 제품의 ID
    """
    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"제품을 찾을 수 없습니다: {product_id}")
        
class ProductValidationError(ProductError):
    """제품 데이터 유효성 검증 실패 시 발생하는 예외
    
    Args:
        message: 오류 메시지
        invalid_fields: 유효하지 않은 필드 목록
    """
    def __init__(self, message: str, invalid_fields: Optional[List[str]] = None):
        self.invalid_fields = invalid_fields or []
        super().__init__(message)
        
class ProductDuplicateError(ProductError):
    """중복된 제품 ID가 발견되었을 때 발생하는 예외
    
    Args:
        product_id: 중복된 제품의 ID
    """
    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"이미 존재하는 제품 ID입니다: {product_id}")
        
class ProductDataError(ProductError):
    """제품 데이터 처리 중 오류가 발생했을 때 발생하는 예외
    
    Args:
        message: 오류 메시지
        source_error: 원인이 된 예외 객체
    """
    def __init__(self, message: str, source_error: Optional[Exception] = None):
        self.source_error = source_error
        super().__init__(f"{message}" + (f": {str(source_error)}" if source_error else ""))

class Product:
    """제품 데이터 모델 클래스
    
    K-Food Timer 애플리케이션에서 제품 데이터를 표현하는 클래스입니다.
    제품의 ID, 이름, 설명, 조리 시간, 이미지 등의 정보를 저장합니다.
    
    Attributes:
        id (str): 제품 고유 ID
        name (dict): 다국어 지원 이름 (예: {"ko": "신라면", "en": "Shin Ramyun"})
        description (dict): 다국어 지원 설명
        category (str): 제품 카테고리
        cook_time (int): 조리 시간(초)
        image (str): 이미지 파일 경로
        manufacturer (str): 제조사
        tags (list): 태그 목록
        favorite (bool): 즐겨찾기 여부
        last_used (datetime): 마지막 사용 일시
        nutrition (dict): 영양 정보
        ingredients (list): 재료 목록
        cooking_steps (list): 조리 단계 목록
        custom_data (dict): 사용자 정의 데이터
    """
    
    def __init__(self, id: str = None, name: Dict[str, str] = None, description: Dict[str, str] = None,
                 category: str = "", cook_time: int = 0, image: str = "", manufacturer: str = "",
                 tags: List[str] = None, favorite: bool = False, last_used: datetime.datetime = None,
                 nutrition: Dict[str, Any] = None, ingredients: List[str] = None,
                 cooking_steps: List[Dict[str, Any]] = None, custom_data: Dict[str, Any] = None):
        """Product 클래스 초기화
        
        Args:
            id: 제품 고유 ID (None인 경우 자동 생성)
            name: 다국어 지원 이름 (예: {"ko": "신라면", "en": "Shin Ramyun"})
            description: 다국어 지원 설명
            category: 제품 카테고리
            cook_time: 조리 시간(초)
            image: 이미지 파일 경로
            manufacturer: 제조사
            tags: 태그 목록
            favorite: 즐겨찾기 여부
            last_used: 마지막 사용 일시
            nutrition: 영양 정보
            ingredients: 재료 목록
            cooking_steps: 조리 단계 목록
            custom_data: 사용자 정의 데이터
            
        Raises:
            ProductValidationError: 필수 필드가 누락되었거나 유효하지 않은 경우
        """
        # 필수 필드 검증
        if id is None:
            id = str(uuid.uuid4())
            
        if name is None or not isinstance(name, dict) or len(name) == 0:
            invalid_fields = ["name"]
            raise ProductValidationError("제품 이름은 필수 필드입니다.", invalid_fields)
            
        self.id = id
        self.name = name
        self.description = description or {}
        self.category = category
        self.cook_time = cook_time
        self.image = image
        self.manufacturer = manufacturer
        self.tags = tags or []
        self.favorite = favorite
        self.last_used = last_used
        self.nutrition = nutrition or {}
        self.ingredients = ingredients or []
        self.cooking_steps = cooking_steps or []
        self.custom_data = custom_data or {}
        
        # 검색 최적화를 위한 키워드 캐싱
        self._search_keywords = None
    
    def get_localized_name(self, language: str = "ko") -> str:
        """지정된 언어로 현지화된 이름 반환
        
        Args:
            language: 언어 코드 (기본값: "ko")
            
        Returns:
            str: 현지화된 이름 (해당 언어가 없으면 첫 번째 언어의 이름)
        """
        if language in self.name:
            return self.name[language]
        # 지정된 언어가 없으면 첫 번째 언어 반환
        return next(iter(self.name.values()), "")
        
    def get_localized_description(self, language: str = "ko") -> str:
        """지정된 언어로 현지화된 설명 반환
        
        Args:
            language: 언어 코드 (기본값: "ko")
            
        Returns:
            str: 현지화된 설명 (해당 언어가 없으면 빈 문자열)
        """
        if language in self.description:
            return self.description[language]
        # 지정된 언어가 없으면 첫 번째 언어 반환
        return next(iter(self.description.values()), "")
        
    def validate(self) -> bool:
        """제품 데이터 유효성 검증
        
        Returns:
            bool: 유효성 검증 결과
            
        Raises:
            ProductValidationError: 유효하지 않은 필드가 있는 경우
        """
        invalid_fields = []
        
        # 필수 필드 검증
        if not self.id:
            invalid_fields.append("id")
            
        if not self.name or not isinstance(self.name, dict) or len(self.name) == 0:
            invalid_fields.append("name")
            
        # 조리 시간은 0 이상이어야 함
        if self.cook_time < 0:
            invalid_fields.append("cook_time")
            
        # 유효하지 않은 필드가 있으면 예외 발생
        if invalid_fields:
            raise ProductValidationError(f"제품 데이터 유효성 검증 실패: {', '.join(invalid_fields)}", invalid_fields)
            
        return True
        
    def to_dict(self) -> Dict[str, Any]:
        """Product 객체를 딕셔너리로 변환
        
        Returns:
            dict: 제품 데이터를 표현하는 딕셔너리
        """
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "cook_time": self.cook_time,
            "image": self.image,
            "manufacturer": self.manufacturer,
            "tags": self.tags,
            "favorite": self.favorite,
            "nutrition": self.nutrition,
            "ingredients": self.ingredients,
            "cooking_steps": self.cooking_steps,
            "custom_data": self.custom_data
        }
        
        # None이 아닌 경우에만 last_used 포함
        if self.last_used:
            result["last_used"] = self.last_used.isoformat()
            
        return result
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """딕셔너리에서 Product 객체 생성
        
        Args:
            data: 제품 데이터를 표현하는 딕셔너리
            
        Returns:
            Product: 생성된 Product 객체
            
        Raises:
            ProductValidationError: 필수 필드가 누락되었거나 유효하지 않은 경우
        """
        # last_used가 있으면 datetime으로 변환
        last_used = None
        if "last_used" in data and data["last_used"]:
            try:
                last_used = datetime.datetime.fromisoformat(data["last_used"])
            except (ValueError, TypeError) as e:
                logger.warning(f"last_used 필드 변환 실패: {data.get('id', 'unknown')}, 값: {data.get('last_used')}")
                # 오류가 있어도 객체 생성은 계속 진행
                    
        # Product 객체 생성
        return cls(
            id=data.get("id"),
            name=data.get("name", {}),
            description=data.get("description", {}),
            category=data.get("category", ""),
            cook_time=data.get("cook_time", 0),
            image=data.get("image", ""),
            manufacturer=data.get("manufacturer", ""),
            tags=data.get("tags", []),
            favorite=data.get("favorite", False),
            last_used=last_used,
            nutrition=data.get("nutrition", {}),
            ingredients=data.get("ingredients", []),
            cooking_steps=data.get("cooking_steps", []),
            custom_data=data.get("custom_data", {})
        )
        
    def get_search_keywords(self) -> List[str]:
        """검색에 사용할 키워드 목록 반환 (최적화)
        
        제품의 이름, 설명, 제조사, 태그 등에서 검색 키워드를 추출합니다.
        결과를 캐싱하여 반복적인 검색 성능을 개선합니다.
        
        Returns:
            list: 검색 키워드 목록
        """
        # 캐시된 키워드가 있으면 반환
        if self._search_keywords is not None:
            return self._search_keywords
            
        # 검색 키워드 생성
        keywords = []
        
        # 이름 추가
        for name in self.name.values():
            keywords.append(name.lower())
            
        # 설명 추가
        for desc in self.description.values():
            keywords.append(desc.lower())
            
        # 제조사 추가
        if self.manufacturer:
            keywords.append(self.manufacturer.lower())
            
        # 카테고리 추가
        if self.category:
            keywords.append(self.category.lower())
            
        # 태그 추가
        keywords.extend([tag.lower() for tag in self.tags])
        
        # 결과 캐싱
        self._search_keywords = keywords
        
        return keywords
        
    def __str__(self) -> str:
        """Product 객체의 문자열 표현
        
        Returns:
            str: Product 객체의 문자열 표현
        """
        return f"Product({self.id}: {self.get_localized_name()})"
        
    def __eq__(self, other) -> bool:
        """두 Product 객체가 같은지 비교
        
        Args:
            other: 비교할 객체
            
        Returns:
            bool: 같은 객체인지 여부
        """
        if not isinstance(other, Product):
            return False
        return self.id == other.id
        
    def __hash__(self) -> int:
        """Product 객체의 해시 값
        
        Returns:
            int: 해시 값
        """
        return hash(self.id)

class ProductDataInterface(ABC):
    """제품 데이터 액세스를 위한 인터페이스 
    
    이 인터페이스는 다양한 데이터 저장소(파일, 데이터베이스 등)에 대한
    일관된 접근 방식을 제공하기 위한 추상 기본 클래스입니다.
    ProductManager 클래스는 이 인터페이스를 구현합니다.
    
    이 인터페이스를 사용하면 향후 다른 데이터 저장소로 전환하거나
    다양한 저장소 구현을 테스트하기 쉬워집니다.
    """
    
    @abstractmethod
    def load_products(self) -> bool:
        """제품 데이터 로드
        
        Returns:
            bool: 로드 성공 여부
        """
        pass
        
    @abstractmethod
    def save_products(self, force: bool = False) -> bool:
        """제품 데이터 저장
        
        Args:
            force: 강제 저장 여부
            
        Returns:
            bool: 저장 성공 여부
        """
        pass
        
    @abstractmethod
    def get_all_products(self) -> List[Product]:
        """모든 제품 조회
        
        Returns:
            list: 모든 Product 객체 리스트
        """
        pass
        
    @abstractmethod
    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """ID로 제품 조회
        
        Args:
            product_id: 조회할 제품 ID
            
        Returns:
            Product: 찾은 Product 객체 또는 None
        """
        pass
        
    @abstractmethod
    def add_product(self, product: Product) -> bool:
        """새 제품 추가
        
        Args:
            product: 추가할 Product 객체
            
        Returns:
            bool: 추가 성공 여부
        """
        pass
        
    @abstractmethod
    def update_product(self, product_id: str, updated_data: Dict[str, Any]) -> bool:
        """제품 정보 업데이트
        
        Args:
            product_id: 업데이트할 제품 ID
            updated_data: 업데이트할 데이터
            
        Returns:
            bool: 업데이트 성공 여부
        """
        pass
        
    @abstractmethod
    def delete_product(self, product_id: str) -> bool:
        """제품 삭제
        
        Args:
            product_id: 삭제할 제품 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        pass

class ProductManager(ProductDataInterface):
    """제품 관리 클래스
    
    제품 데이터의 로드, 저장, 검색, 필터링 등의 기능을 제공합니다.
    ProductDataInterface를 구현하여 데이터 액세스 표준화를 제공합니다.
    """
    
    def __init__(self, data_path: str = "data/products.json"):
        """ProductManager 초기화
        
        Args:
            data_path: 제품 데이터 파일 경로
        """
        self.data_path = data_path
        self.products = []  # Product 객체 리스트
        self._ensure_data_dir()
        
        # 인덱스 생성 (최적화)
        self._id_index = {}  # id -> product 매핑
        self._category_index = {}  # category -> [products] 매핑
        
        # 마지막 저장/로드 시간 기록
        self._last_load_time = None
        self._last_save_time = None
        self._file_modified_time = None
        
    def _ensure_data_dir(self) -> None:
        """데이터 디렉토리 존재 확인 및 생성
        
        Raises:
            ProductDataError: 디렉토리 생성 실패 시 발생
        """
        data_dir = os.path.dirname(self.data_path)
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
                logger.info(f"데이터 디렉토리 생성: {data_dir}")
            except OSError as e:
                raise ProductDataError(f"데이터 디렉토리 생성 실패: {data_dir}", e)
    
    def _build_indexes(self) -> None:
        """검색 및 필터링 최적화를 위한 인덱스 구축 (최적화)"""
        # ID 인덱스 구축
        self._id_index = {product.id: product for product in self.products}
        
        # 카테고리 인덱스 구축
        self._category_index = {}
        for product in self.products:
            if product.category not in self._category_index:
                self._category_index[product.category] = []
            self._category_index[product.category].append(product)
    
    @contextlib.contextmanager
    def _open_data_file(self, mode='r'):
        """데이터 파일을 안전하게 열고 닫는 컨텍스트 매니저 (리소스 관리)
        
        Args:
            mode: 파일 열기 모드 ('r' 또는 'w')
            
        Yields:
            file: 열린 파일 객체
            
        Raises:
            ProductDataError: 파일 열기 실패 시 발생
        """
        file = None
        try:
            file = open(self.data_path, mode, encoding=DEFAULT_ENCODING)
            yield file
        except (IOError, OSError) as e:
            raise ProductDataError(f"파일 {self.data_path} 접근 오류", e)
        finally:
            if file:
                file.close()
                
    def _is_file_modified(self) -> bool:
        """데이터 파일이 마지막 로드 이후 수정되었는지 확인 (리소스 관리)
        
        Returns:
            bool: 파일 수정 여부
        """
        if not os.path.exists(self.data_path):
            return False
            
        try:
            current_mtime = os.path.getmtime(self.data_path)
            if self._file_modified_time is None or current_mtime > self._file_modified_time:
                self._file_modified_time = current_mtime
                return True
            return False
        except OSError as e:
            logger.warning(f"파일 수정 시간 확인 실패: {e}")
            return True  # 오류 발생 시 안전하게 수정된 것으로 간주
            
    def load_products(self) -> bool:
        """제품 데이터 로드
        
        JSON 파일에서 제품 데이터를 읽어 products 리스트에 Product 객체로 저장합니다.
        
        Returns:
            bool: 로드 성공 여부
            
        Raises:
            ProductDataError: 데이터 로드 중 오류 발생 시
        """
        # 파일이 존재하지 않으면 기본 데이터 생성
        if not os.path.exists(self.data_path):
            logger.warning(f"제품 데이터 파일이 없습니다: {self.data_path}")
            self._create_default_products()
            return True
            
        # 파일이 수정되지 않았으면 다시 로드하지 않음 (리소스 관리)
        if not self._is_file_modified() and self.products:
            logger.debug("데이터 파일이 수정되지 않았습니다. 기존 데이터를 유지합니다.")
            return True
            
        try:
            with self._open_data_file('r') as f:
                data = json.load(f)
                
            # 데이터 타입 확인 및 처리
            if isinstance(data, list):
                # 대용량 데이터 처리를 위한 배치 처리 (리소스 관리)
                if len(data) > MAX_LOAD_BATCH_SIZE:
                    logger.info(f"대용량 데이터({len(data)}개)를 배치 처리합니다.")
                    self.products = []
                    for i in range(0, len(data), MAX_LOAD_BATCH_SIZE):
                        batch = data[i:i + MAX_LOAD_BATCH_SIZE]
                        try:
                            self.products.extend([Product.from_dict(item) for item in batch])
                        except ProductValidationError as e:
                            logger.warning(f"일부 제품 데이터 로드 실패: {e}")
                else:
                    valid_products = []
                    for product_data in data:
                        try:
                            valid_products.append(Product.from_dict(product_data))
                        except ProductValidationError as e:
                            logger.warning(f"제품 데이터 로드 실패: {e}")
                            
                    self.products = valid_products
                    
                logger.info(f"{len(self.products)}개의 제품 데이터를 로드했습니다.")
                
                # 인덱스 구축 (최적화)
                self._build_indexes()
                
                # 마지막 로드 시간 기록
                self._last_load_time = datetime.datetime.now()
                return True
            else:
                logger.error("데이터 파일 형식이 올바르지 않습니다.")
                self._create_default_products()
                return False
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            # 파일 손상 시 초기 데이터 생성
            self._create_default_products()
            raise ProductDataError("JSON 데이터 파싱 실패", e)
        except ProductDataError:
            # 이미 ProductDataError인 경우는 다시 래핑하지 않고 그대로 전파
            self._create_default_products()
            raise
        except Exception as e:
            logger.error(f"제품 데이터 로드 중 오류 발생: {e}")
            # 파일 손상 시 초기 데이터 생성
            self._create_default_products()
            raise ProductDataError("제품 데이터 로드 중 예상치 못한 오류", e)
    
    def save_products(self, force: bool = False) -> bool:
        """제품 데이터 저장
        
        products 리스트의 Product 객체를 JSON 형식으로 파일에 저장합니다.
        
        Args:
            force: 강제 저장 여부
            
        Returns:
            bool: 저장 성공 여부
            
        Raises:
            ProductDataError: 데이터 저장 중 오류 발생 시
        """
        # 마지막 로드 이후 변경이 없으면 저장하지 않음 (최적화)
        if not force and self._last_save_time and self._last_load_time and self._last_save_time > self._last_load_time:
            logger.debug("데이터 변경이 없습니다. 저장을 건너뜁니다.")
            return True
            
        try:
            # 대용량 데이터 처리를 위한 스트리밍 저장 (리소스 관리)
            product_count = len(self.products)
            if product_count > MAX_LOAD_BATCH_SIZE:
                logger.info(f"대용량 데이터({product_count}개)를 스트리밍 방식으로 저장합니다.")
                return self._save_products_streaming()
                
            # 일반적인 경우 한 번에 저장
            data = [product.to_dict() for product in self.products]
            
            with self._open_data_file('w') as f:
                json.dump(data, f, ensure_ascii=False, indent=DEFAULT_JSON_INDENT)
                
            # 마지막 저장 시간 기록
            self._last_save_time = datetime.datetime.now()
            self._file_modified_time = os.path.getmtime(self.data_path)
            
            logger.info(f"{len(self.products)}개의 제품 데이터를 저장했습니다.")
            return True
        except (json.JSONDecodeError, TypeError) as e:
            error_msg = "JSON 직렬화 오류"
            logger.error(f"{error_msg}: {e}")
            raise ProductDataError(error_msg, e)
        except ProductDataError:
            # 이미 ProductDataError인 경우는 다시 래핑하지 않고 그대로 전파
            raise
        except Exception as e:
            error_msg = "제품 데이터 저장 중 오류 발생"
            logger.error(f"{error_msg}: {e}")
            raise ProductDataError(error_msg, e)
            
    def _save_products_streaming(self) -> bool:
        """대용량 제품 데이터를 스트리밍 방식으로 저장 (리소스 관리)
        
        대용량 데이터를 메모리 효율적으로 저장하기 위한 메서드입니다.
        
        Returns:
            bool: 저장 성공 여부
            
        Raises:
            ProductDataError: 스트리밍 저장 중 오류 발생 시
        """
        try:
            with self._open_data_file('w') as f:
                # JSON 배열 시작
                f.write('[\n')
                
                # 제품 데이터 순회하며 저장
                for i, product in enumerate(self.products):
                    product_json = json.dumps(product.to_dict(), ensure_ascii=False, indent=DEFAULT_JSON_INDENT)
                    
                    if i > 0:
                        f.write(',\n')
                    f.write(product_json)
                    
                # JSON 배열 종료
                f.write('\n]')
                
            # 마지막 저장 시간 기록
            self._last_save_time = datetime.datetime.now()
            self._file_modified_time = os.path.getmtime(self.data_path)
            
            logger.info(f"{len(self.products)}개의 제품 데이터를 스트리밍 방식으로 저장했습니다.")
            return True
        except Exception as e:
            error_msg = "스트리밍 저장 중 오류 발생"
            logger.error(f"{error_msg}: {e}")
            raise ProductDataError(error_msg, e)
            
    def reload_if_needed(self) -> bool:
        """필요한 경우에만 데이터 다시 로드 (리소스 관리)
        
        파일이 외부에서 수정된 경우에만 데이터를 다시 로드합니다.
        
        Returns:
            bool: 다시 로드 여부
        """
        if self._is_file_modified():
            logger.info("데이터 파일이 외부에서 수정되었습니다. 데이터를 다시 로드합니다.")
            return self.load_products()
        return False
    
    def get_all_products(self) -> List[Product]:
        """모든 제품 조회
        
        Returns:
            list: 모든 Product 객체 리스트
        """
        return self.products
        
    def iter_products(self) -> Iterator[Product]:
        """메모리 효율적인 제품 이터레이터 제공 (리소스 관리)
        
        대용량 데이터 처리 시 메모리 효율을 위한 이터레이터입니다.
        
        Yields:
            Product: 제품 객체
        """
        for product in self.products:
            yield product
        
    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """ID로 제품 조회 (최적화)
        
        Args:
            product_id: 조회할 제품 ID
            
        Returns:
            Product: 찾은 Product 객체 또는 None
        """
        # 인덱스 사용 (O(1) 시간 복잡도)
        return self._id_index.get(product_id)
        
    def get_product_by_id_strict(self, product_id: str) -> Product:
        """ID로 제품 조회 (엄격 모드)
        
        Args:
            product_id: 조회할 제품 ID
            
        Returns:
            Product: 찾은 Product 객체
            
        Raises:
            ProductNotFoundError: 제품을 찾을 수 없을 때 발생
        """
        product = self._id_index.get(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        return product
        
    def filter_products(self, filter_func: Callable[[Product], bool]) -> List[Product]:
        """필터 함수를 사용하여 제품 필터링
        
        Args:
            filter_func: 필터링에 사용할 함수
            
        Returns:
            list: 필터링된 Product 객체 리스트
        """
        return [product for product in self.products if filter_func(product)]
        
    def filter_products_iter(self, filter_func: Callable[[Product], bool]) -> Generator[Product, None, None]:
        """메모리 효율적인 제품 필터링 이터레이터 (리소스 관리)
        
        Args:
            filter_func: 필터링에 사용할 함수
            
        Yields:
            Product: 필터링된 제품 객체
        """
        for product in self.products:
            if filter_func(product):
                yield product

    def get_products_by_category(self, category: str) -> List[Product]:
        """카테고리로 제품 필터링 (최적화)
        
        Args:
            category: 필터링할 카테고리
            
        Returns:
            list: 필터링된 Product 객체 리스트
        """
        # 인덱스 사용 (O(1) 시간 복잡도)
        return self._category_index.get(category, [])
        
    @lru_cache(maxsize=8)  # 성능 최적화: 자주 조회하는 즐겨찾기 및 최근 항목 캐싱
    def get_favorite_products(self) -> List[Product]:
        """즐겨찾기 제품 조회 (최적화)
        
        Returns:
            list: 즐겨찾기된 Product 객체 리스트
        """
        return self.filter_products(lambda p: p.favorite)
        
    def get_recent_products(self, limit: int = 5) -> List[Product]:
        """최근 사용한 제품 조회
        
        Args:
            limit: 최대 개수
            
        Returns:
            list: 최근 사용한 순으로 정렬된 Product 객체 리스트
        """
        # last_used가 있는 제품만 필터링하고 날짜 기준으로 내림차순 정렬
        used_products = self.filter_products(lambda p: p.last_used is not None)
        used_products.sort(key=lambda p: p.last_used, reverse=True)
        return used_products[:limit]
        
    @lru_cache(maxsize=1)  # 성능 최적화: 카테고리 목록 캐싱
    def get_categories(self) -> List[str]:
        """모든 카테고리 조회 (최적화)
        
        Returns:
            list: 카테고리 문자열 리스트 (중복 제거, 정렬됨)
        """
        # 인덱스 사용 (O(1) 시간 복잡도)
        return sorted(self._category_index.keys())
        
    def add_product(self, product: Product) -> bool:
        """새 제품 추가
        
        Args:
            product: 추가할 Product 객체
            
        Returns:
            bool: 추가 성공 여부
            
        Raises:
            ProductDuplicateError: 이미 존재하는 제품 ID인 경우
            ProductValidationError: 제품 데이터 유효성 검증 실패 시
        """
        # ID 중복 검사
        if self.get_product_by_id(product.id):
            raise ProductDuplicateError(product.id)
            
        try:
            # 제품 정보 검증
            product.validate()
            
            # 제품 추가
            self.products.append(product)
            
            # 인덱스 업데이트 (최적화)
            self._id_index[product.id] = product
            if product.category not in self._category_index:
                self._category_index[product.category] = []
            self._category_index[product.category].append(product)
            
            # 캐시 무효화
            self.get_favorite_products.cache_clear()
            self.get_categories.cache_clear()
            
            logger.info(f"새 제품이 추가되었습니다: {product.id} ({product.get_localized_name()})")
            return True
        except ProductValidationError:
            # 이미 적절한 예외이므로 다시 발생시킵니다
            raise
        except Exception as e:
            # 다른 예상치 못한 오류는 ProductError로 래핑
            logger.error(f"제품 추가 중 오류 발생: {e}")
            raise ProductError(f"제품 추가 실패: {str(e)}")
            
    def update_product(self, product_id: str, updated_data: Dict[str, Any]) -> bool:
        """제품 정보 업데이트
        
        Args:
            product_id: 업데이트할 제품 ID
            updated_data: 업데이트할 데이터
            
        Returns:
            bool: 업데이트 성공 여부
            
        Raises:
            ProductNotFoundError: 제품을 찾을 수 없을 때 발생
            ProductValidationError: 업데이트된 데이터 유효성 검증 실패 시
        """
        product = self.get_product_by_id(product_id)
        if not product:
            raise ProductNotFoundError(product_id)
            
        try:
            old_category = product.category
            
            # 업데이트할 속성만 변경
            for key, value in updated_data.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            
            # 제품 정보 검증
            product.validate()
            
            # 카테고리가 변경된 경우 인덱스 업데이트 (최적화)
            if 'category' in updated_data and old_category != product.category:
                # 이전 카테고리에서 제거
                if old_category in self._category_index:
                    self._category_index[old_category].remove(product)
                    
                # 새 카테고리에 추가
                if product.category not in self._category_index:
                    self._category_index[product.category] = []
                self._category_index[product.category].append(product)
                
                # 캐시 무효화
                self.get_categories.cache_clear()
            
            # 즐겨찾기 상태가 변경된 경우 캐시 무효화
            if 'favorite' in updated_data:
                self.get_favorite_products.cache_clear()
                
            # 검색 키워드 캐시 초기화
            product._search_keywords = None
            
            logger.info(f"제품 정보가 업데이트되었습니다: {product_id}")
            return True
        except ProductValidationError:
            # 이미 적절한 예외이므로 다시 발생시킵니다
            raise
        except AttributeError as e:
            # 유효하지 않은 필드 업데이트 시도
            invalid_field = str(e).split("'")[1] if "'" in str(e) else "알 수 없음"
            logger.error(f"유효하지 않은 필드 업데이트 시도: {invalid_field}")
            raise ProductValidationError(f"유효하지 않은 필드: {invalid_field}", [invalid_field])
        except Exception as e:
            # 다른 예상치 못한 오류는 ProductError로 래핑
            logger.error(f"제품 업데이트 중 오류 발생: {e}")
            raise ProductError(f"제품 업데이트 실패: {str(e)}")
            
    def delete_product(self, product_id: str) -> bool:
        """제품 삭제
        
        Args:
            product_id: 삭제할 제품 ID
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            ProductNotFoundError: 제품을 찾을 수 없을 때 발생
        """
        product = self.get_product_by_id(product_id)
        if not product:
            raise ProductNotFoundError(product_id)
            
        # 리스트에서 제거
        self.products.remove(product)
        
        # 인덱스에서 제거 (최적화)
        del self._id_index[product_id]
        if product.category in self._category_index:
            self._category_index[product.category].remove(product)
            
        # 캐시 무효화
        self.get_favorite_products.cache_clear()
        self.get_categories.cache_clear()
        
        logger.info(f"제품이 삭제되었습니다: {product_id}")
        return True
        
    def search_products(self, query: str) -> List[Product]:
        """제품 검색 (최적화)
        
        제품 이름, 설명, 제조사, 태그 등에서 검색어를 포함하는 제품을 찾습니다.
        
        Args:
            query: 검색어
            
        Returns:
            list: 검색 결과 Product 객체 리스트
        """
        if not query or not isinstance(query, str):
            return []
            
        query = query.lower()
        
        # 캐시된 키워드 사용하여 검색 (최적화)
        return [product for product in self.products 
                if any(query in keyword for keyword in product.get_search_keywords())]
                
    def search_products_iter(self, query: str) -> Generator[Product, None, None]:
        """메모리 효율적인 검색 이터레이터 (리소스 관리)
        
        대용량 데이터에서 검색 시 메모리 효율을 위한 이터레이터입니다.
        
        Args:
            query: 검색어
            
        Yields:
            Product: 검색 결과 제품 객체
        """
        if not query or not isinstance(query, str):
            return
            
        query = query.lower()
        
        for product in self.products:
            if any(query in keyword for keyword in product.get_search_keywords()):
                yield product

    def _create_default_products(self) -> None:
        """기본 제품 데이터 생성
        
        앱 첫 실행 시 또는 데이터 파일 손상 시 기본 제품 데이터를 생성합니다.
        """
        logger.info("기본 제품 데이터를 생성합니다.")
        self.products = []
        
        # 카테고리별 기본 제품 추가
        self.products.extend(self._get_default_ramen_products())
        self.products.extend(self._get_default_rice_products())
        self.products.extend(self._get_default_frozen_products())
        
        # 인덱스 구축 (최적화)
        self._build_indexes()
        
        # 저장
        self.save_products(force=True)
        
        logger.info(f"{len(self.products)}개의 기본 제품 데이터가 생성되었습니다.")

    def _get_default_ramen_products(self) -> List[Product]:
        """기본 라면류 제품 데이터 생성
        
        Returns:
            list: 라면류 Product 객체 리스트
        """
        return [
            Product(
                name={"ko": "신라면", "en": "Shin Ramyun"},
                category="라면류",
                cook_time=180,  # 3분
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
                tags=["매운맛", "국물", "국내 라면"]
            ),
            Product(
                name={"ko": "진라면 매운맛", "en": "Jin Ramen Spicy"},
                category="라면류",
                cook_time=180,  # 3분
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
                name={"ko": "참깨라면", "en": "Sesame Ramen"},
                category="라면류",
                cook_time=180,  # 3분
                manufacturer="삼양식품",
                description={"ko": "참깨향이 특징인 라면", "en": "Ramen with sesame flavor"},
                instructions=[
                    {"ko": "물 550ml를 냄비에 넣고 끓인다", "en": "Boil 550ml of water in a pot"},
                    {"ko": "면과 스프를 넣는다", "en": "Add noodles and soup powder"},
                    {"ko": "3분간 더 끓인다", "en": "Boil for 3 more minutes"},
                    {"ko": "불을 끄고 그릇에 담아 먹는다", "en": "Turn off heat and serve"}
                ],
                tags=["고소한맛", "참깨"]
            )
        ]
        
    def _get_default_rice_products(self) -> List[Product]:
        """기본 즉석밥 제품 데이터 생성
        
        Returns:
            list: 즉석밥 Product 객체 리스트
        """
        return [
            Product(
                name={"ko": "햇반", "en": "Cooked White Rice"},
                category="즉석밥/국류",
                cook_time=90,  # 1분 30초
                manufacturer="CJ제일제당",
                description={"ko": "전자레인지에 데워 먹는 즉석밥", "en": "Microwavable instant cooked rice"},
                image_url="https://example.com/images/hatban.jpg",
                barcode="8801007458342",
                instructions=[
                    {"ko": "포장의 한쪽 모서리를 1~2cm 개봉한다", "en": "Open one corner of the package 1-2cm"},
                    {"ko": "전자레인지에 1분 30초간 가열한다", "en": "Heat in microwave for 1 minute and 30 seconds"},
                    {"ko": "잘 섞어서 먹는다", "en": "Mix well and serve"}
                ],
                featured=True,
                tags=["즉석밥", "간편식", "주식"]
            ),
            Product(
                name={"ko": "곤드레나물밥", "en": "Gondre Herb Rice"},
                category="즉석밥/국류",
                cook_time=120,  # 2분
                manufacturer="오뚜기",
                description={"ko": "곤드레나물이 들어간 즉석밥", "en": "Instant rice with Gondre herb"},
                instructions=[
                    {"ko": "포장의 한쪽 모서리를 1~2cm 개봉한다", "en": "Open one corner of the package 1-2cm"},
                    {"ko": "전자레인지에 2분간 가열한다", "en": "Heat in microwave for 2 minutes"},
                    {"ko": "잘 섞어서 먹는다", "en": "Mix well and serve"}
                ],
                tags=["즉석밥", "나물밥", "건강식"]
            ),
            Product(
                name={"ko": "흑미밥", "en": "Black Rice"},
                category="즉석밥/국류",
                cook_time=90,  # 1분 30초
                manufacturer="CJ제일제당",
                description={"ko": "흑미가 들어간 건강한 즉석밥", "en": "Healthy instant rice with black rice"},
                instructions=[
                    {"ko": "포장의 한쪽 모서리를 1~2cm 개봉한다", "en": "Open one corner of the package 1-2cm"},
                    {"ko": "전자레인지에 1분 30초간 가열한다", "en": "Heat in microwave for 1 minute and 30 seconds"},
                    {"ko": "잘 섞어서 먹는다", "en": "Mix well and serve"}
                ],
                tags=["즉석밥", "흑미", "건강식"]
            )
        ]
        
    def _get_default_frozen_products(self) -> List[Product]:
        """기본 냉동식품 제품 데이터 생성
        
        Returns:
            list: 냉동식품 Product 객체 리스트
        """
        return [
            Product(
                name={"ko": "비비고 만두", "en": "Bibigo Dumplings"},
                category="냉동식품",
                cook_time=300,  # 5분
                manufacturer="CJ제일제당",
                description={"ko": "맛있는 냉동 만두", "en": "Delicious frozen dumplings"},
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
                name={"ko": "해물파전", "en": "Seafood Pancake"},
                category="냉동식품",
                cook_time=480,  # 8분
                manufacturer="풀무원",
                description={"ko": "전자레인지에 데워 먹는 해물파전", "en": "Microwavable seafood pancake"},
                instructions=[
                    {"ko": "포장을 제거한다", "en": "Remove packaging"},
                    {"ko": "전자레인지에 4분간 가열한다", "en": "Heat in microwave for 4 minutes"},
                    {"ko": "뒤집어서 4분간 더 가열한다", "en": "Flip and heat for 4 more minutes"}
                ],
                tags=["냉동식품", "해물", "파전", "간식"]
            ),
            Product(
                name={"ko": "김치볶음밥", "en": "Kimchi Fried Rice"},
                category="냉동식품",
                cook_time=360,  # 6분
                manufacturer="풀무원",
                description={"ko": "전자레인지에 데워 먹는 김치볶음밥", "en": "Microwavable kimchi fried rice"},
                instructions=[
                    {"ko": "포장을 뜯고 비닐랩을 벗긴다", "en": "Remove packaging and plastic wrap"},
                    {"ko": "전자레인지에 6분간 가열한다", "en": "Heat in microwave for 6 minutes"},
                    {"ko": "잘 저어서 먹는다", "en": "Mix well and serve"}
                ],
                favorite=True,
                tags=["냉동식품", "볶음밥", "김치", "간편식"]
            )
        ]

    # 단위 테스트 지원을 위한 메서드들

    def create_test_instance(cls, test_data_path: str = None) -> 'ProductManager':
        """테스트용 ProductManager 인스턴스 생성
        
        단위 테스트에서 사용할 수 있는 격리된 ProductManager 인스턴스를 생성합니다.
        
        Args:
            test_data_path: 테스트용 데이터 파일 경로 (None인 경우 임시 경로 사용)
            
        Returns:
            ProductManager: 테스트용 ProductManager 인스턴스
        """
        import tempfile
        import os
        
        # 테스트 데이터 경로가 주어지지 않은 경우 임시 파일 사용
        if test_data_path is None:
            temp_dir = tempfile.gettempdir()
            test_data_path = os.path.join(temp_dir, f"test_products_{uuid.uuid4()}.json")
        
        # 테스트용 인스턴스 생성
        return cls(data_path=test_data_path)

    def reset_for_test(self) -> None:
        """테스트를 위한 상태 초기화
        
        단위 테스트에서 매 테스트 케이스 실행 전 상태를 초기화할 때 사용합니다.
        """
        self.products = []
        self._id_index = {}
        self._category_index = {}
        self._last_load_time = None
        self._last_save_time = None
        self._file_modified_time = None
        
        # 캐시 초기화
        self.get_favorite_products.cache_clear()
        self.get_categories.cache_clear()
        
        # 데이터 파일이 있으면 삭제
        if os.path.exists(self.data_path):
            try:
                os.remove(self.data_path)
                logger.debug(f"테스트를 위해 데이터 파일을 삭제했습니다: {self.data_path}")
            except OSError as e:
                logger.warning(f"테스트 데이터 파일 삭제 실패: {e}")

    def add_test_products(self, count: int = 5) -> List[Product]:
        """테스트용 제품 데이터 추가
        
        단위 테스트에서 사용할 수 있는 테스트 제품 데이터를 생성하고 추가합니다.
        
        Args:
            count: 생성할 테스트 제품 수
            
        Returns:
            list: 생성된 Product 객체 리스트
        """
        test_products = []
        categories = ["테스트라면", "테스트밥", "테스트냉동"]
        
        for i in range(count):
            # 제품 ID 생성
            product_id = f"test-{uuid.uuid4()}"
            
            # 카테고리 선택 (순환)
            category = categories[i % len(categories)]
            
            # 테스트 제품 생성
            product = Product(
                id=product_id,
                name={"ko": f"테스트 제품 {i+1}", "en": f"Test Product {i+1}"},
                description={"ko": f"테스트 설명 {i+1}", "en": f"Test description {i+1}"},
                category=category,
                cook_time=180 + i * 30,  # 3분 + 증분
                manufacturer="테스트 제조사",
                tags=[f"tag{i+1}", "test"]
            )
            
            # 짝수 번호 제품은 즐겨찾기로 설정
            if i % 2 == 0:
                product.favorite = True
            
            # 제품 추가
            self.add_product(product)
            test_products.append(product)
        
        return test_products

    def create_test_product() -> Product:
        """테스트용 단일 제품 객체 생성
        
        단위 테스트에서 사용할 수 있는 테스트 제품 객체를 생성합니다.
        
        Returns:
            Product: 테스트용 Product 객체
        """
        return Product(
            id=f"test-{uuid.uuid4()}",
            name={"ko": "테스트 제품", "en": "Test Product"},
            description={"ko": "테스트 설명", "en": "Test description"},
            category="테스트 카테고리",
            cook_time=180,
            manufacturer="테스트 제조사",
            tags=["test", "sample"]
        )

    # 클래스 메서드로 등록
    ProductManager.create_test_instance = classmethod(create_test_instance)
    ProductManager.create_test_product = staticmethod(create_test_product)

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
    for product in manager.filter_products(lambda p: p.featured):
        print(f"- {product} (특집)")
            
    # 새 제품 추가 예제
    new_product = Product(
        name={"ko": "새우맛라면", "en": "Shrimp Flavored Ramen"},
        category="라면류",
        cook_time=180,
        manufacturer="농심",
        description={"ko": "새우 맛이 특징인 라면", "en": "Ramen with delicious shrimp flavor"},        
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