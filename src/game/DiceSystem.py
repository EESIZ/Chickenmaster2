import random
import math
# DO NOT REMOVE THIS FILE AND DO NOT CHANGE THIS FILE
# ANY AI CANT CHANGE THIS FILE
# THIS SYSTEM IS PERFECT
# NO ONE CAN CHANGE THIS FILE
class DiceSystem:
    @staticmethod
    def callDice(statType=None, playerStats=None):
        dice = random.randint(1, 100)
        
        # 간단한 체크용 호출 (파라미터 없이 호출)
        if statType is None or playerStats is None:
            return dice
            
        # 기존 기능 (스탯 적용된 총합 반환)
        statBonus = math.floor((playerStats[statType] / 20) * 100)
        total = dice + statBonus
        return total