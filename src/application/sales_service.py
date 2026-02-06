import random
from typing import List, Dict, Tuple
from uuid import UUID
from collections import defaultdict

from core.ports.sales_port import SalesPort, SalesResult, CustomerFeedback
from core.ports.repository_port import RepositoryPort
from core.domain.player import Player
from core.domain.competitor import Competitor
from core.domain.value_objects import Money, Percentage
from core.domain.customer import MarketAverages, CustomerAI


class SalesService(SalesPort):
    """판매 서비스 구현체"""

    def __init__(self, repository: RepositoryPort):
        self._repository = repository

    def calculate_daily_sales(self, players: List[Player], competitors: List[Competitor]) -> Dict[UUID, SalesResult]:
        """일일 판매량 계산"""

        # 1. 시장 평균 계산 (가격, 품질, 인지도)
        market_averages = self._calculate_market_averages(players, competitors)

        # 2. 총 고객 수 결정 (상권 데이터 가정, 임시로 1000명 고정)
        # TODO: 상권 데이터 연동
        total_population = 1000
        ai_customer_count = int(total_population * 0.1)  # 10%
        numeric_customer_count = total_population - ai_customer_count

        # 3. 참여자별 점수 및 점유율 계산 (수치적 고객용)
        participant_scores = self._calculate_participant_scores(players, competitors, market_averages)
        total_score = sum(participant_scores.values())

        # 4. 결과 컨테이너 초기화
        results: Dict[UUID, SalesResult] = {}
        participant_sales: Dict[UUID, int] = defaultdict(int)  # ID -> 판매량
        participant_revenue: Dict[UUID, int] = defaultdict(int) # ID -> 매출
        participant_feedbacks: Dict[UUID, List[CustomerFeedback]] = defaultdict(list)

        # 5. AI 고객 (10%) 개별 시뮬레이션
        # 저장소에서 AI 고객 로드 (없으면 임시 생성)
        # 성능을 위해 매번 생성하지 않고 저장소에서 가져와야 하지만,
        # 현재는 간소화를 위해 매번 생성하거나 로직 내에서 처리
        for _ in range(ai_customer_count):
            self._simulate_ai_customer(
                players, competitors, market_averages,
                participant_sales, participant_revenue, participant_feedbacks
            )

        # 6. 수치적 고객 (90%) 배분
        if total_score > 0:
            for p_id, score in participant_scores.items():
                market_share = score / total_score
                # 욕구 반영 (임시로 50% 확률로 구매한다고 가정 - README 규칙 구현 필요)
                # README: 매턴 [욕구]% 확률로 구매. 수치적 고객은 점유율에 따름.
                # 여기서는 간단히 점유율대로 배분하되, 전체 구매율을 50%로 가정
                buying_customers = int(numeric_customer_count * market_share * 0.5)

                # 평균 객단가 계산
                avg_price = self._get_average_price(p_id, players, competitors)

                participant_sales[p_id] += buying_customers
                participant_revenue[p_id] += buying_customers * avg_price

        # 7. 최종 결과 생성
        total_buyers = sum(participant_sales.values())

        all_participants = players + competitors # type: ignore
        for participant in all_participants:
            sales_count = participant_sales[participant.id]
            revenue = participant_revenue[participant.id]
            feedbacks = participant_feedbacks[participant.id]

            market_share = sales_count / total_buyers if total_buyers > 0 else 0.0

            # 판매된 제품 상세 (임시로 대표 제품 하나에 몰아주기)
            sold_products = {}
            if sales_count > 0:
                # 첫 번째 매장의 첫 번째 제품 찾기
                store = self._repository.get_store(participant.store_ids[0])
                if store and store.product_ids:
                    sold_products[store.product_ids[0]] = sales_count

            results[participant.id] = SalesResult(
                total_revenue=revenue,
                total_customers=sales_count,
                sold_products=sold_products,
                feedbacks=feedbacks,
                market_share=market_share
            )

        return results

    def _calculate_market_averages(self, players: List[Player], competitors: List[Competitor]) -> MarketAverages:
        """시장 평균 데이터 계산"""
        total_price = 0
        total_quality = 0
        total_awareness = 0
        count = 0

        all_participants = players + competitors # type: ignore
        for p in all_participants:
            # 각 참여자의 매장 -> 제품 순회
            for store_id in p.store_ids:
                store = self._repository.get_store(store_id)
                if not store: continue

                for product_id in store.product_ids:
                    product = self._repository.get_product(product_id)
                    if not product: continue

                    # 품질 계산을 위해 요리 스탯 필요 (플레이어만 해당, 경쟁자는 기본값)
                    cooking_stat = 0
                    if isinstance(p, Player):
                        stats = p.get_effective_stats()
                        cooking_stat = stats.cooking.base_value
                    else:
                        cooking_stat = 50 # 경쟁자 기본값

                    total_price += product.selling_price.amount
                    total_quality += product.calculate_quality(cooking_stat)
                    total_awareness += product.awareness
                    count += 1

        if count == 0:
            return MarketAverages(Money(0), 0, 0)

        return MarketAverages(
            average_price=Money(total_price // count),
            average_quality=total_quality / count,
            average_awareness=total_awareness / count
        )

    def _calculate_participant_scores(self, players, competitors, market_averages) -> Dict[UUID, float]:
        """참여자별 종합 점수 계산 (수치적 고객 배분용)"""
        scores = {}
        all_participants = players + competitors

        for p in all_participants:
            p_score = 0.0
            product_count = 0

            for store_id in p.store_ids:
                store = self._repository.get_store(store_id)
                if not store: continue

                for product_id in store.product_ids:
                    product = self._repository.get_product(product_id)
                    if not product: continue

                    cooking_stat = 0
                    if isinstance(p, Player):
                         cooking_stat = p.get_effective_stats().cooking.base_value
                    else:
                        cooking_stat = 50

                    # 제품 점수 계산 (Product 엔티티의 메서드 활용)
                    # Note: Product.calculate_comprehensive_score 메서드는
                    # calculate_quality 내부에서 cooking_stat을 인자로 받지 않고 0으로 처리하는 구조임.
                    # 정확한 계산을 위해 직접 계산

                    price_score = product.calculate_price_score(market_averages.average_price)
                    quality_score = product.calculate_quality_score(market_averages.average_quality) # 요리 스탯 미반영 한계
                    # 보정: 요리 스탯 반영한 품질 점수 재계산
                    real_quality = product.calculate_quality(cooking_stat)
                    if market_averages.average_quality > 0:
                        quality_score = (real_quality / market_averages.average_quality) * 100
                    else:
                        quality_score = 100

                    awareness_score = product.calculate_awareness_score(market_averages.average_awareness)

                    p_score += (price_score + quality_score + awareness_score)
                    product_count += 1

            # 평균 점수
            if product_count > 0:
                scores[p.id] = p_score / product_count
            else:
                scores[p.id] = 0.0

        return scores

    def _simulate_ai_customer(self, players, competitors, market_averages, sales, revenue, feedbacks):
        """AI 고객 1명의 구매 결정 시뮬레이션"""

        # 임시 AI 고객 생성 (랜덤 성향)
        ai_customer = CustomerAI(
            id=UUID(int=0), # Dummy
            name="손님",
            price_sensitivity=random.random(),
            quality_preference=random.random(),
            brand_loyalty=random.random(),
            desire=Percentage(random.randint(0, 100))
        )

        # 구매 여부 결정 (욕구 기반)
        if random.randint(0, 100) > ai_customer.desire.value:
            return # 구매 안함

        # 매장(참여자) 선택
        best_score = -1
        best_participant = None
        best_product = None

        all_participants = players + competitors
        random.shuffle(all_participants) # 순서 섞어서 공평하게

        for p in all_participants:
            for store_id in p.store_ids:
                store = self._repository.get_store(store_id)
                if not store: continue

                for product_id in store.product_ids:
                    product = self._repository.get_product(product_id)
                    if not product: continue

                    cooking_stat = 0
                    if isinstance(p, Player):
                        cooking_stat = p.get_effective_stats().cooking.base_value
                    else:
                        cooking_stat = 50

                    quality = product.calculate_quality(cooking_stat)

                    score = ai_customer.evaluate_product(
                        product.selling_price,
                        quality,
                        product.awareness,
                        market_averages
                    )

                    if score > best_score:
                        best_score = score
                        best_participant = p
                        best_product = product

        # 구매 처리
        if best_participant and best_product:
            sales[best_participant.id] += 1
            revenue[best_participant.id] += best_product.selling_price.amount

            # 피드백 생성 (롤러코스터 타이쿤 스타일)
            self._generate_feedback(ai_customer, best_product, best_score, feedbacks[best_participant.id])

    def _generate_feedback(self, customer: CustomerAI, product, score: float, feedback_list: List[CustomerFeedback]):
        """고객 피드백 생성"""
        # 확률적으로 피드백 남김 (10%)
        if random.random() > 0.1:
            return

        korean_names = ["김철수", "이영희", "박민수", "최지우", "정우성", "강동원", "아이유", "유재석"]
        name = random.choice(korean_names)

        if score > 80:
            msgs = [
                "이 집 치킨은 정말 최고야!",
                "가성비가 훌륭하네요.",
                "친구들에게 추천하고 싶어요.",
                "사장님이 친절해요 (아마도?)."
            ]
            sentiment = "POSITIVE"
        elif score < 40:
            msgs = [
                "치킨이 너무 비싸요.",
                "맛이 좀 이상한데요...",
                "여기 다시는 안 올 것 같아요.",
                "다른 가게 갈걸."
            ]
            sentiment = "NEGATIVE"
        else:
            msgs = [
                "그저 그렇네요.",
                "나쁘지 않아요.",
                "배고파서 먹었어요."
            ]
            sentiment = "NEUTRAL"

        feedback_list.append(CustomerFeedback(
            customer_name=name,
            message=random.choice(msgs),
            sentiment=sentiment,
            product_name=product.name
        ))

    def _get_average_price(self, participant_id: UUID, players, competitors) -> int:
        """참여자의 평균 판매가 조회"""
        participant = next((p for p in players + competitors if p.id == participant_id), None)
        if not participant: return 0

        total_price = 0
        count = 0
        for store_id in participant.store_ids:
            store = self._repository.get_store(store_id)
            if store:
                for product_id in store.product_ids:
                    product = self._repository.get_product(product_id)
                    if product:
                        total_price += product.selling_price.amount
                        count += 1

        return total_price // count if count > 0 else 0
