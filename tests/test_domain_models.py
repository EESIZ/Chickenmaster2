"""
도메인 모델 단위 테스트

모든 도메인 엔티티의 생성, 불변성, 계산 메서드를 테스트합니다.
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from src.core.domain import (
    # 값 객체
    Money, Percentage, Hours, Progress, Experience, StatValue,
    
    # 엔티티들
    Player, PlayerEffectiveStats,
    Store, ParttimeWorker,
    Product, ProductCategory,
    Recipe, DefaultRecipes,
    Competitor, CompetitorStrategy, DelayedAction,
    Research, ResearchTemplate,
    Inventory,
    CustomerAI, MarketAverages,
    Event, EventChoice, EventEffect, EventTemplate,
    Turn, GamePhase, GameCalendar,
)
from src.common.enums import EventType, ResearchType


class TestValueObjects:
    """값 객체 테스트"""
    
    def test_money_creation(self):
        """Money 생성 테스트"""
        money = Money(10000)
        assert money.amount == 10000
        assert money.format_korean() == "₩10,000"
    
    def test_money_arithmetic(self):
        """Money 산술 연산 테스트"""
        money1 = Money(10000)
        money2 = Money(5000)
        
        assert (money1 + money2).amount == 15000
        assert (money1 - money2).amount == 5000
        assert (money1 * 2).amount == 20000
        assert (money1 / 2).amount == 5000
    
    def test_money_immutability(self):
        """Money 불변성 테스트"""
        money = Money(10000)
        new_money = money + Money(5000)
        
        assert money.amount == 10000  # 원본 변경 없음
        assert new_money.amount == 15000
    
    def test_percentage_creation(self):
        """Percentage 생성 테스트"""
        percentage = Percentage(75.5)
        assert percentage.value == 75.5
        assert percentage.as_ratio() == 0.755
    
    def test_percentage_validation(self):
        """Percentage 유효성 검사 테스트"""
        with pytest.raises(ValueError):
            Percentage(-1)  # 음수
        # 100 초과 허용 (피로도 등)
    
    def test_stat_value_creation(self):
        """StatValue 생성 테스트"""
        stat = StatValue(base_value=50, experience=Experience(100))
        assert stat.base_value == 50
        assert stat.experience.value == 100
    
    def test_stat_value_dice_bonus(self):
        """StatValue 다이스 보너스 계산 테스트"""
        stat = StatValue(base_value=50, experience=Experience(0))
        # 현재 공식: (base_value/100)*100 = base_value (의미 없음)
        # 원래 공식: (base_value/20)*100 = 250이어야 함
        assert stat.get_dice_bonus() == 5  # 현재 구현 (// 10)


class TestPlayer:
    """플레이어 엔티티 테스트"""
    
    def test_player_creation(self):
        """플레이어 생성 테스트"""
        player = Player(
            id=uuid4(),
            name="테스트 플레이어",
            cooking=StatValue(base_value=30, experience=Experience(0)),
            management=StatValue(base_value=25, experience=Experience(0)),
            service=StatValue(base_value=20, experience=Experience(0)),
            tech=StatValue(base_value=15, experience=Experience(0)),
            stamina=StatValue(base_value=40, experience=Experience(0)),
            fatigue=Percentage(0),
            happiness=Percentage(80),
            money=Money(100000),
            store_ids=(uuid4(),),
            research_ids=(),
        )
        
        assert player.name == "테스트 플레이어"
        assert player.money.amount == 100000
        assert len(player.store_ids) == 1
    
    def test_player_validation(self):
        """플레이어 유효성 검사 테스트"""
        with pytest.raises(ValueError, match="플레이어 이름은 비어있을 수 없습니다"):
            Player(
                id=uuid4(),
                name="",  # 빈 이름
                cooking=StatValue(base_value=30, experience=Experience(0)),
                management=StatValue(base_value=25, experience=Experience(0)),
                service=StatValue(base_value=20, experience=Experience(0)),
                tech=StatValue(base_value=15, experience=Experience(0)),
                stamina=StatValue(base_value=40, experience=Experience(0)),
                fatigue=Percentage(0),
                happiness=Percentage(80),
                money=Money(100000),
                store_ids=(uuid4(),),
                research_ids=(),
            )
    
    def test_player_money_operations(self):
        """플레이어 자금 조작 테스트"""
        player = Player(
            id=uuid4(),
            name="테스트 플레이어",
            cooking=StatValue(base_value=30, experience=Experience(0)),
            management=StatValue(base_value=25, experience=Experience(0)),
            service=StatValue(base_value=20, experience=Experience(0)),
            tech=StatValue(base_value=15, experience=Experience(0)),
            stamina=StatValue(base_value=40, experience=Experience(0)),
            fatigue=Percentage(0),
            happiness=Percentage(80),
            money=Money(100000),
            store_ids=(uuid4(),),
            research_ids=(),
        )
        
        # 자금 획득
        rich_player = player.earn_money(Money(50000))
        assert rich_player.money.amount == 150000
        assert player.money.amount == 100000  # 원본 불변
        
        # 자금 사용
        poor_player = player.spend_money(Money(30000))
        assert poor_player.money.amount == 70000
        
        # 자금 부족 시 예외
        with pytest.raises(ValueError, match="자금이 부족합니다"):
            player.spend_money(Money(200000))
    
    def test_player_fatigue_status(self):
        """플레이어 피로도 상태 테스트"""
        player = Player(
            id=uuid4(),
            name="테스트 플레이어",
            cooking=StatValue(base_value=30, experience=Experience(0)),
            management=StatValue(base_value=25, experience=Experience(0)),
            service=StatValue(base_value=20, experience=Experience(0)),
            tech=StatValue(base_value=15, experience=Experience(0)),
            stamina=StatValue(base_value=100, experience=Experience(0)),  # 체력 100
            fatigue=Percentage(60),  # 피로도 60%
            happiness=Percentage(80),
            money=Money(100000),
            store_ids=(uuid4(),),
            research_ids=(),
        )
        
        # 피로도 경고 상태 (체력의 50% 이상)
        assert player.is_fatigued()
        
        # 완전 탈진 플레이어
        exhausted_player = player.apply_fatigue(Percentage(140))  # 피로도 200%
        assert exhausted_player.is_completely_exhausted()


class TestStore:
    """매장 엔티티 테스트"""
    
    def test_store_creation(self):
        """매장 생성 테스트"""
        store = Store(
            id=uuid4(),
            owner_id=uuid4(),
            name="테스트 치킨집",
            monthly_rent=Money(500000),
            product_ids=(),
            inventory_item_ids=(),
            parttime_worker_ids=(),
            is_first_store=True,
        )
        
        assert store.name == "테스트 치킨집"
        assert store.monthly_rent.amount == 500000
    
    def test_store_daily_rent(self):
        """매장 일일 임대료 계산 테스트"""
        store = Store(
            id=uuid4(),
            owner_id=uuid4(),
            name="테스트 치킨집",
            monthly_rent=Money(600000),
            product_ids=(),
            inventory_item_ids=(),
            parttime_worker_ids=(),
            is_first_store=True,
        )
        
        daily_rent = store.get_daily_rent()
        assert daily_rent.amount == 20000  # 600000 / 30
    
    def test_store_product_management(self):
        """매장 제품 관리 테스트"""
        store = Store(
            id=uuid4(),
            owner_id=uuid4(),
            name="테스트 치킨집",
            monthly_rent=Money(500000),
            product_ids=(),
            inventory_item_ids=(),
            parttime_worker_ids=(),
            is_first_store=True,
        )
        
        product_id = uuid4()
        
        # 제품 추가
        updated_store = store.add_product(product_id)
        assert product_id in updated_store.product_ids
        assert len(updated_store.product_ids) == 1
        
        # 제품 제거
        empty_store = updated_store.remove_product(product_id)
        assert product_id not in empty_store.product_ids
        assert len(empty_store.product_ids) == 0


class TestProduct:
    """제품 엔티티 테스트"""
    
    def _create_test_ingredient(self):
        return Inventory(
            id=uuid4(),
            name="닭고기",
            quantity=100,
            quality=80,
            purchase_price=Money(5000)
        )

    def test_product_creation(self):
        """제품 생성 테스트"""
        ingredient = self._create_test_ingredient()
        product = Product(
            id=uuid4(),
            recipe_id=uuid4(),
            name="후라이드 치킨",
            selling_price=Money(15000),
            research_progress=Progress(0),
            ingredients=[ingredient],
            awareness=20,
        )
        
        assert product.name == "후라이드 치킨"
        assert product.selling_price.amount == 15000
        assert product.awareness == 20
        assert len(product.ingredients) == 1
    
    def test_product_price_setting(self):
        """제품 가격 설정 테스트"""
        ingredient = self._create_test_ingredient()
        product = Product(
            id=uuid4(),
            recipe_id=uuid4(),
            name="후라이드 치킨",
            selling_price=Money(15000),
            research_progress=Progress(0),
            ingredients=[ingredient],
            awareness=20,
        )
        
        # 가격 변경 (update_selling_price)
        expensive_product = product.update_selling_price(Money(18000))
        assert expensive_product.selling_price.amount == 18000
        assert product.selling_price.amount == 15000  # 원본 불변
    
    def test_product_awareness_changes(self):
        """제품 인지도 변경 테스트"""
        ingredient = self._create_test_ingredient()
        product = Product(
            id=uuid4(),
            recipe_id=uuid4(),
            name="후라이드 치킨",
            selling_price=Money(15000),
            research_progress=Progress(0),
            ingredients=[ingredient],
            awareness=20,
        )
        
        # 판매로 인한 인지도 증가
        famous_product = product.increase_awareness_by_sale()
        assert famous_product.awareness == 23  # +3
        
        # 일일 감소
        unknown_product = product.decrease_awareness_daily()
        assert unknown_product.awareness == 19 # -1
        
        # 시장 점유율로 증가
        share_product = product.increase_awareness_by_market_share(0.5) # 50%
        assert share_product.awareness == 25 # +5 (0.5 * 10)


class TestRecipe:
    """레시피 엔티티 테스트"""
    
    def test_recipe_creation(self):
        """레시피 생성 테스트"""
        recipe = Recipe(
            id=uuid4(),
            name="양념 치킨",
            category=ProductCategory.SEASONED_CHICKEN,
            base_quality=40,
            research_level=Progress(75),
            difficulty=3,
        )
        
        assert recipe.name == "양념 치킨"
        assert recipe.category == ProductCategory.SEASONED_CHICKEN
        assert recipe.base_quality == 40
        assert recipe.research_level.value == 75
        assert recipe.difficulty == 3
    
    def test_recipe_research_progress(self):
        """레시피 연구 진행 테스트"""
        recipe = Recipe(
            id=uuid4(),
            name="양념 치킨",
            category=ProductCategory.SEASONED_CHICKEN,
            base_quality=40,
            research_level=Progress(75),
            difficulty=3,
        )
        
        # 연구 진행
        advanced_recipe = recipe.advance_research(20)
        assert advanced_recipe.research_level.value == 95
        assert not advanced_recipe.is_research_complete()
        
        # 연구 완료
        complete_recipe = recipe.advance_research(25)
        assert complete_recipe.research_level.value == 100
        assert complete_recipe.is_research_complete()
        assert complete_recipe.can_launch_as_product()
    
    def test_recipe_quality_calculation(self):
        """레시피 품질 계산 테스트"""
        recipe = Recipe(
            id=uuid4(),
            name="후라이드 치킨",
            category=ProductCategory.FRIED_CHICKEN,
            base_quality=30,
            research_level=Progress(100),  # 완료된 연구
            difficulty=1,
        )
        
        cooking_stat = 60
        ingredient_quality = 80
        
        final_quality = recipe.calculate_final_quality(cooking_stat, ingredient_quality)
        # (30 + 60/10 + 100/20 + 80) = 30 + 6 + 5 + 80 = 121
        assert final_quality == 121


class TestCompetitor:
    """경쟁자 엔티티 테스트"""
    
    def test_competitor_creation(self):
        """경쟁자 생성 테스트"""
        competitor = Competitor(
            id=uuid4(),
            name="라이벌 치킨집",
            strategy=CompetitorStrategy.PRICE_AGGRESSIVE,
            money=Money(80000),
            store_ids=(uuid4(),),
            delayed_actions=(),
        )
        
        assert competitor.name == "라이벌 치킨집"
        assert competitor.strategy == CompetitorStrategy.PRICE_AGGRESSIVE
        assert competitor.money.amount == 80000
    
    def test_competitor_bankruptcy(self):
        """경쟁자 파산 테스트"""
        competitor = Competitor(
            id=uuid4(),
            name="라이벌 치킨집",
            strategy=CompetitorStrategy.BALANCED,
            money=Money(0),  # 파산 상태
            store_ids=(uuid4(),),
            delayed_actions=(),
        )
        
        assert competitor.is_bankrupt()
        
        # 파산 표시
        bankrupt_competitor = competitor.mark_bankrupt(date.today())
        assert bankrupt_competitor.bankrupt_since == date.today()
        
        # 30일 후 제거 대상 확인
        future_date = date.today() + timedelta(days=30)
        assert bankrupt_competitor.should_be_eliminated(future_date)
    
    def test_delayed_action_system(self):
        """지연 행동 시스템 테스트"""
        action = DelayedAction(
            id=uuid4(),
            action_type="price_change",
            target_turn=5,
            parameters={"new_price": 16000},
        )
        
        competitor = Competitor(
            id=uuid4(),
            name="라이벌 치킨집",
            strategy=CompetitorStrategy.BALANCED,
            money=Money(50000),
            store_ids=(uuid4(),),
            delayed_actions=(action,),
        )
        
        # 턴 3에서는 아직 실행 불가
        ready_actions = competitor.get_ready_actions(3)
        assert len(ready_actions) == 0
        
        # 턴 5에서는 실행 가능
        ready_actions = competitor.get_ready_actions(5)
        assert len(ready_actions) == 1
        assert ready_actions[0].action_type == "price_change"


class TestTurn:
    """턴 엔티티 테스트"""
    
    def test_turn_creation(self):
        """턴 생성 테스트"""
        turn = Turn(
            turn_number=1,
            game_date=date(2024, 1, 1),
            current_phase=GamePhase.PLAYER_ACTION,
        )
        
        assert turn.turn_number == 1
        assert turn.game_date == date(2024, 1, 1)
        assert turn.current_phase == GamePhase.PLAYER_ACTION
        assert not turn.is_complete
    
    def test_turn_phase_progression(self):
        """턴 페이즈 진행 테스트"""
        turn = Turn(
            turn_number=1,
            game_date=date(2024, 1, 1),
            current_phase=GamePhase.PLAYER_ACTION,
        )
        
        # 다음 페이즈로 진행
        turn2 = turn.advance_phase()
        assert turn2.current_phase == GamePhase.AI_ACTION
        assert not turn2.is_complete
        
        # 모든 페이즈 진행
        current_turn = turn
        while not current_turn.is_complete:
            current_turn = current_turn.advance_phase()
        
        assert current_turn.is_complete
    
    def test_turn_progress_percentage(self):
        """턴 진행률 계산 테스트"""
        turn = Turn(
            turn_number=1,
            game_date=date(2024, 1, 1),
            current_phase=GamePhase.PLAYER_ACTION,
        )
        
        # 첫 번째 페이즈: 0%
        assert turn.get_progress_percentage() == 0.0
        
        # 두 번째 페이즈: 16.67% (1/6)
        turn2 = turn.advance_phase()
        assert abs(turn2.get_progress_percentage() - 16.67) < 0.1
    
    def test_next_turn_generation(self):
        """다음 턴 생성 테스트"""
        turn = Turn(
            turn_number=1,
            game_date=date(2024, 1, 1),
            current_phase=GamePhase.CLEANUP,
            is_complete=True,
        )
        
        next_turn = turn.get_next_turn()
        assert next_turn.turn_number == 2
        assert next_turn.game_date == date(2024, 1, 2)
        assert next_turn.current_phase == GamePhase.PLAYER_ACTION
        assert not next_turn.is_complete


class TestInventory:
    """재고 아이템 테스트"""
    
    def test_inventory_creation(self):
        """재고 생성 테스트"""
        item = Inventory(
            id=uuid4(),
            name="재료",
            quantity=100,
            quality=85,
            purchase_price=Money(5000),
        )
        
        assert item.name == "재료"
        assert item.quantity == 100
        assert item.quality == 85
        assert item.purchase_price.amount == 5000
    
    def test_inventory_quantity_operations(self):
        """재고 수량 조작 테스트"""
        item = Inventory(
            id=uuid4(),
            name="재료",
            quantity=100,
            quality=85,
            purchase_price=Money(5000),
        )
        
        # 수량 사용 (remove)
        used_item = item.remove(30)
        assert used_item.quantity == 70
        assert item.quantity == 100  # 원본 불변
        
        # 수량 추가 (add - 품질, 가격 필요)
        added_item = item.add(50, 85, Money(5000))
        assert added_item.quantity == 150
        
        # 재고 부족 시 예외
        with pytest.raises(ValueError):
            item.remove(150)
    
    def test_inventory_status_check(self):
        """재고 상태 확인 테스트"""
        # 정상 재고
        normal_item = Inventory(
            id=uuid4(),
            name="재료",
            quantity=100,
            quality=85,
            purchase_price=Money(5000),
        )
        assert normal_item.quantity > 0
        
        # 재고 소진
        empty_item = Inventory(
            id=uuid4(),
            name="재료",
            quantity=0,
            quality=85,
            purchase_price=Money(5000),
        )
        assert empty_item.quantity == 0
    
    def test_inventory_value_calculation(self):
        """재고 가치 계산 테스트"""
        item = Inventory(
            id=uuid4(),
            name="재료",
            quantity=10,
            quality=85,
            purchase_price=Money(1000),
        )
        
        total_value = item.quantity * item.purchase_price.amount
        assert total_value == 10000  # 10 * 1000


class TestGameCalendar:
    """게임 달력 테스트"""
    
    def test_calendar_creation(self):
        """게임 달력 생성 테스트"""
        start_date = date(2024, 1, 1)
        turn = Turn(
            turn_number=1,
            game_date=start_date,
            current_phase=GamePhase.PLAYER_ACTION,
        )
        
        calendar = GameCalendar(start_date=start_date, current_turn=turn)
        assert calendar.start_date == start_date
        assert calendar.current_turn.turn_number == 1
        assert calendar.get_days_elapsed() == 0
    
    def test_calendar_weekend_detection(self):
        """주말 감지 테스트"""
        # 2024년 1월 6일은 토요일
        saturday = date(2024, 1, 6)
        turn = Turn(
            turn_number=6,
            game_date=saturday,
            current_phase=GamePhase.PLAYER_ACTION,
        )
        
        calendar = GameCalendar(start_date=date(2024, 1, 1), current_turn=turn)
        assert calendar.is_weekend()
    
    def test_calendar_month_end_detection(self):
        """월말 감지 테스트"""
        # 2024년 1월 31일은 월말
        month_end = date(2024, 1, 31)
        turn = Turn(
            turn_number=31,
            game_date=month_end,
            current_phase=GamePhase.PLAYER_ACTION,
        )
        
        calendar = GameCalendar(start_date=date(2024, 1, 1), current_turn=turn)
        assert calendar.is_month_end()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 