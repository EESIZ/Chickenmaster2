/**
 * 주사위 시스템 클래스
 * 플레이어의 스탯을 기반으로 주사위 굴리기를 처리합니다.
 */
class DiceSystem {
    /**
     * 주사위를 굴리고 스탯 보너스를 적용합니다.
     * @param {string} statType - 사용할 스탯 타입
     * @param {number} targetValue - 목표값
     * @param {Object} playerStats - 플레이어 스탯 객체
     * @returns {Object} 주사위 결과 정보
     */
    static CallDice(statType, targetValue, playerStats) {
        const dice = Math.floor(Math.random() * 100) + 1;
        const statBonus = Math.floor((playerStats[statType] / 20) * 100);
        const total = dice + statBonus;
        
        return {
            dice,
            statBonus,
            total,
            success: total >= targetValue,
            statType,
            targetValue
        };
    }
}

module.exports = DiceSystem; 