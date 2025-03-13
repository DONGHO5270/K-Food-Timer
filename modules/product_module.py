#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
한국 간편식품 제품 데이터를 관리하는 모듈
"""

import os
import json
import datetime

class Product:
    """제품 클래스"""
    
    def __init__(self, id, name, category, cooking_time, description="", image_path="", instructions=None):
        """제품 초기화
        
        Args:
            id (str): 제품 ID
            name (str): 제품 이름
            category (str): 제품 카테고리 (라면, 냉동식품, 즉석밥 등)
            cooking_time (int): 조리 시간(초)
            description (str, optional): 제품 설명
            image_path (str, optional): 제품 이미지 경로
            instructions (list, optional): 조리 방법 단계별 설명
        """
        self.id = id
        self.name = name
        self.category = category
        self.cooking_time = cooking_time
        self.description = description
        self.image_path = image_path
        self.instructions = instructions or []
        self.favorite = False
        self.last_used = None
    
    def to_dict(self):
        """제품 정보를 딕셔너리로 변환"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "cooking_time": self.cooking_time,
            "description": self.description,
            "image_path": self.image_path,
            "instructions": self.instructions,
            "favorite": self.favorite,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """딕셔너리에서 제품 객체 생성
        
        Args:
            data (dict): 제품 데이터 딕셔너리
            
        Returns:
            Product: 생성된 제품 객체
        """
        product = cls(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            cooking_time=data["cooking_time"],
            description=data.get("description", ""),
            image_path=data.get("image_path", ""),
            instructions=data.get("instructions", [])
        )
        product.favorite = data.get("favorite", False)
        
        last_used = data.get("last_used")
        if last_used:
            try:
                product.last_used = datetime.datetime.fromisoformat(last_used)
            except (ValueError, TypeError):
                product.last_used = None
        
        return product
    
    def mark_as_used(self):
        """제품 사용 기록 업데이트"""
        self.last_used = datetime.datetime.now()
    
    def toggle_favorite(self):
        """즐겨찾기 상태 전환"""
        self.favorite = not self.favorite
        return self.favorite


class ProductManager:
    """제품 관리 클래스"""
    
    def __init__(self, data_path="data/products.json"):
        """제품 관리자 초기화
        
        Args:
            data_path (str, optional): 제품 데이터 파일 경로
        """
        self.data_path = data_path
        self.products = {}
        self.categories = set()
    
    def load_products(self):
        """제품 데이터 파일에서 제품 정보 로드"""
        if not os.path.exists(self.data_path):
            # 기본 데이터 파일이 없으면 샘플 데이터 생성
            self._create_sample_data()
            return
            
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.products = {}
            for product_data in data:
                product = Product.from_dict(product_data)
                self.products[product.id] = product
                self.categories.add(product.category)
                
            print(f"{len(self.products)}개의 제품 데이터를 로드했습니다.")
        except Exception as e:
            print(f"제품 데이터 로드 중 오류 발생: {e}")
            # 오류 발생 시 샘플 데이터 생성
            self._create_sample_data()
    
    def save_products(self):
        """제품 데이터를 파일에 저장"""
        try:
            # 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            
            data = [product.to_dict() for product in self.products.values()]
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"{len(self.products)}개의 제품 데이터를 저장했습니다.")
        except Exception as e:
            print(f"제품 데이터 저장 중 오류 발생: {e}")
    
    def _create_sample_data(self):
        """샘플 제품 데이터 생성"""
        sample_products = [
            {
                "id": "ramen001",
                "name": "신라면",
                "category": "라면",
                "cooking_time": 180,
                "description": "매운맛이 특징인 대표적인 한국 라면",
                "image_path": "",
                "instructions": [
                    "물 550ml를 냄비에 넣고 끓인다",
                    "면과 스프를 넣는다",
                    "3분간 더 끓인다",
                    "불을 끄고 그릇에 담아 먹는다"
                ]
            },
            {
                "id": "rice001",
                "name": "햇반",
                "category": "즉석밥",
                "cooking_time": 90,
                "description": "전자레인지에 데워 먹는 즉석밥",
                "image_path": "",
                "instructions": [
                    "포장의 한쪽 모서리를 1~2cm 개봉한다",
                    "전자레인지에 1분 30초간 가열한다",
                    "잘 섞어서 먹는다"
                ]
            },
            {
                "id": "frozen001",
                "name": "비비고 만두",
                "category": "냉동식품",
                "cooking_time": 300,
                "description": "맛있는 냉동 만두",
                "image_path": "",
                "instructions": [
                    "팬에 기름을 두른다",
                    "만두를 넣고 중불에서 2분간 굽는다",
                    "물 1/4컵을 붓고 뚜껑을 덮는다",
                    "3분간 더 익힌다"
                ]
            }
        ]
        
        self.products = {}
        self.categories = set()
        
        for product_data in sample_products:
            product = Product.from_dict(product_data)
            self.products[product.id] = product
            self.categories.add(product.category)
        
        self.save_products()
        print("샘플 제품 데이터를 생성했습니다.")
    
    def get_product(self, product_id):
        """ID로 제품 정보 조회
        
        Args:
            product_id (str): 제품 ID
            
        Returns:
            Product: 제품 객체 또는 None
        """
        return self.products.get(product_id)
    
    def get_all_products(self):
        """모든 제품 목록 반환
        
        Returns:
            list: 제품 객체 목록
        """
        return list(self.products.values())
    
    def get_products_by_category(self, category):
        """카테고리별 제품 목록 반환
        
        Args:
            category (str): 제품 카테고리
            
        Returns:
            list: 해당 카테고리의 제품 객체 목록
        """
        return [p for p in self.products.values() if p.category == category]
    
    def get_favorite_products(self):
        """즐겨찾기 제품 목록 반환
        
        Returns:
            list: 즐겨찾기된 제품 객체 목록
        """
        return [p for p in self.products.values() if p.favorite]
    
    def get_recent_products(self, limit=5):
        """최근 사용한 제품 목록 반환
        
        Args:
            limit (int, optional): 반환할 제품 수
            
        Returns:
            list: 최근 사용한 제품 객체 목록
        """
        recent = [p for p in self.products.values() if p.last_used is not None]
        recent.sort(key=lambda p: p.last_used, reverse=True)
        return recent[:limit]
    
    def add_product(self, product):
        """제품 추가
        
        Args:
            product (Product): 추가할 제품 객체
            
        Returns:
            bool: 추가 성공 여부
        """
        if product.id in self.products:
            return False
            
        self.products[product.id] = product
        self.categories.add(product.category)
        return True
    
    def update_product(self, product):
        """제품 정보 업데이트
        
        Args:
            product (Product): 업데이트할 제품 객체
            
        Returns:
            bool: 업데이트 성공 여부
        """
        if product.id not in self.products:
            return False
            
        self.products[product.id] = product
        self.categories = set(p.category for p in self.products.values())
        return True
    
    def delete_product(self, product_id):
        """제품 삭제
        
        Args:
            product_id (str): 삭제할 제품 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        if product_id not in self.products:
            return False
            
        del self.products[product_id]
        self.categories = set(p.category for p in self.products.values())
        return True
    
    def get_categories(self):
        """모든 제품 카테고리 목록 반환
        
        Returns:
            list: 카테고리 목록
        """
        return sorted(list(self.categories)) 