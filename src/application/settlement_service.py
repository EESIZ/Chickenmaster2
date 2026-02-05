from core.ports.settlement_port import SettlementPort, SettlementResult
from core.ports.repository_port import RepositoryPort
from core.domain.player import Player
from core.domain.value_objects import Money


class SettlementService(SettlementPort):
    """정산 서비스 구현체"""

    def __init__(self, repository: RepositoryPort):
        self._repository = repository

    def calculate_settlement(self, player: Player, revenue: int) -> SettlementResult:
        """정산 처리"""

        # 1. 고정 비용 계산 (임대료)
        total_rent = 0
        for store_id in player.store_ids:
            store = self._repository.get_store(store_id)
            if store:
                # 일일 임대료 = 월세 // 30
                total_rent += (store.monthly_rent.amount // 30)

        # 2. 변동 비용 계산 (재료비)
        # TODO: 실제 판매된 제품 데이터를 받아와서 정확히 계산해야 함
        # 현재는 매출의 40%를 재료비로 추정 (간소화)
        ingredient_cost = int(revenue * 0.4)

        # 3. 인건비 계산
        # TODO: 알바생/점장 시스템 연동
        labor_cost = 0

        # 4. 유지보수비
        maintenance_cost = 0 # 랜덤 이벤트나 장비 상태에 따라 변동

        total_cost = total_rent + ingredient_cost + labor_cost + maintenance_cost
        net_profit = revenue - total_cost

        # 5. 플레이어 자금 업데이트
        updated_player = player
        if net_profit > 0:
            updated_player = updated_player.earn_money(Money(net_profit))
        elif net_profit < 0:
            # 적자 발생 - 자금이 부족해도 강제 차감 (부채 시스템이 있다면)
            # 현재 Money 클래스는 음수 차감을 지원하지 않으므로 (spend_money가 에러냄)
            # 보유 자금 내에서만 차감하거나, Money 객체를 수정해야 함.
            # 하지만 앞서 Money 클래스에 is_negative 허용했으므로,
            # Player.spend_money 로직을 확인해야 함.
            # Player.spend_money는 자금 부족 시 에러를 냄.
            # 따라서 빚을 지게 하려면 별도 메서드가 필요하거나 예외 처리 필요.
            # 여기서는 자금 부족 시 0원이 되고 파산 처리 로직이 필요.

            loss = abs(net_profit)
            if updated_player.money.amount >= loss:
                updated_player = updated_player.spend_money(Money(loss))
            else:
                # 자금 부족 - 0원으로 만들고 파산 플래그? (미구현)
                updated_player = updated_player.spend_money(updated_player.money)

        self._repository.save_player(updated_player)

        return SettlementResult(
            revenue=revenue,
            rent_cost=total_rent,
            ingredient_cost=ingredient_cost,
            labor_cost=labor_cost,
            maintenance_cost=maintenance_cost,
            total_cost=total_cost,
            net_profit=net_profit,
            updated_player=updated_player
        )
