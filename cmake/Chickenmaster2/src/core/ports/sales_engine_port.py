"""
판매 엔진 포트 인터페이스

가격, 품질, 인지도를 기반으로 한 판매량 계산과 고객 AI 처리를 담당하는 인터페이스입니다.
SalesService가 이 인터페이스를 구현합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID

from core.domain.player import Player
from core.domain.store import Store
from core.domain.product import Product
from core.domain.customer import CustomerAI
from core.domain.value_objects import Money, Percentage


class SalesResult:
    """판매 결과 DTO"""
    def __init__(self, product_id: UUID, units_sold: int, revenue: Money, 
                 customer_feedback: List[str], awareness_increase: Percentage):
        self.product_id = product_id
        self.units_sold = units_sold
        self.revenue = revenue
        self.customer_feedback = customer_feedback
        self.awareness_increase = awareness_increase


class CustomerDecision:
    """고객 구매 결정 DTO"""
    def __init__(self, customer_id: UUID, will_buy: bool, chosen_product_id: Optional[UUID], 
                 decision_factors: Dict[str, float], feedback: str = ""):
        self.customer_id = customer_id
        self.will_buy = will_buy
        self.chosen_product_id = chosen_product_id
        self.decision_factors = decision_factors  # 가격, 품질, 인지도 영향도
        self.feedback = feedback


class SalesEnginePort(ABC):
    """판매 엔진 포트 인터페이스"""
    
    @abstractmethod
    def calculate_daily_sales(self, store: Store, products: List[Product], 
                            customers: List[CustomerAI]) -> List[SalesResult]:
        """일일 판매량을 계산합니다.
        
        README.md 규칙: 가격·품질·인지도 기반 판매 점수 계산
        
        Args:
            store: 매장 정보
            products: 판매할 제품 목록
            customers: 고객 AI 목록
            
        Returns:
            List[SalesResult]: 제품별 판매 결과
        """
        pass
    
    @abstractmethod
    def simulate_customer_decision(self, customer: CustomerAI, store: Store, 
                                 products: List[Product]) -> CustomerDecision:
        """개별 고객의 구매 결정을 시뮬레이션합니다.
        
        README.md 규칙: 10% 개별 AI + 90% 수치 계산
        
        Args:
            customer: 고객 AI
            store: 매장 정보
            products: 선택 가능한 제품 목록
            
        Returns:
            CustomerDecision: 고객의 구매 결정
        """
        pass
    
    @abstractmethod
    def calculate_sales_score(self, product: Product, store: Store) -> float:
        """제품의 판매 점수를 계산합니다.
        
        가격, 품질, 매장 인지도를 종합하여 점수 산출
        
        Args:
            product: 판매 제품
            store: 매장 정보
            
        Returns:
            float: 판매 점수 (0.0 ~ 100.0)
        """
        pass
    
    @abstractmethod
    def apply_bulk_sales_calculation(self, sales_score: float, base_demand: int) -> int:
        """수치 기반 대량 판매 계산을 적용합니다.
        
        README.md 규칙: 90% 수치 계산 부분
        
        Args:
            sales_score: 판매 점수
            base_demand: 기본 수요량
            
        Returns:
            int: 계산된 판매량
        """
        pass
    
    @abstractmethod
    def process_individual_customers(self, customers: List[CustomerAI], store: Store, 
                                   products: List[Product]) -> List[CustomerDecision]:
        """개별 고객 AI 처리를 수행합니다.
        
        README.md 규칙: 10% 개별 AI 처리 부분
        
        Args:
            customers: 고객 AI 목록
            store: 매장 정보
            products: 제품 목록
            
        Returns:
            List[CustomerDecision]: 고객별 구매 결정 목록
        """
        pass
    
    @abstractmethod
    def update_store_awareness(self, store: Store, sales_results: List[SalesResult]) -> Store:
        """판매 결과에 따라 매장 인지도를 업데이트합니다.
        
        Args:
            store: 업데이트할 매장
            sales_results: 판매 결과 목록
            
        Returns:
            Store: 업데이트된 매장
        """
        pass
    
    @abstractmethod
    def reduce_inventory(self, store_id: UUID, sales_results: List[SalesResult]) -> bool:
        """판매 결과에 따라 재고를 차감합니다.
        
        Args:
            store_id: 매장 ID
            sales_results: 판매 결과 목록
            
        Returns:
            bool: 재고 차감 성공 여부
        """
        pass
    
    @abstractmethod
    def generate_customer_feedback(self, customer_decision: CustomerDecision, 
                                 product: Product) -> str:
        """고객 피드백을 생성합니다.
        
        Args:
            customer_decision: 고객 구매 결정
            product: 구매한 제품
            
        Returns:
            str: 고객 피드백 메시지
        """
        pass
    
    @abstractmethod
    def get_market_analysis(self, store: Store, competitors: List[Store]) -> Dict[str, Any]:
        """시장 분석 정보를 제공합니다.
        
        Args:
            store: 분석할 매장
            competitors: 경쟁 매장 목록
            
        Returns:
            Dict[str, Any]: 시장 분석 결과
        """
        pass
    
    @abstractmethod
    def calculate_optimal_price(self, product: Product, store: Store, 
                              market_data: Dict[str, Any]) -> Money:
        """최적 가격을 계산합니다.
        
        Args:
            product: 가격을 계산할 제품
            store: 매장 정보
            market_data: 시장 데이터
            
        Returns:
            Money: 최적 가격
        """
        pass 