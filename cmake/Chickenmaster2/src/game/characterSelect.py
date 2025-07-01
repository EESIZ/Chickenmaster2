from .DiceSystem import DiceSystem
from .Playerstat import PlayerStats

# 게임 시작 - 캐릭터 선택
def characterSelection():
    print("캐릭터를 선택하세요:")
    print("1. 요리사")
    print("2. 경영자") 
    print("3. 서비스 전문가")
    print("0. 테스트맨")
    
    choice = input("선택: ")
    
    if choice == "1":
        preset = characterPresets["chef"]
        return PlayerStats(preset["cooking"], preset["management"], preset["service"], preset["stamina"], preset["tech"])
    elif choice == "2":
        preset = characterPresets["businessman"]
        return PlayerStats(preset["cooking"], preset["management"], preset["service"], preset["stamina"], preset["tech"])
    elif choice == "3":
        preset = characterPresets["service_expert"]
        return PlayerStats(preset["cooking"], preset["management"], preset["service"], preset["stamina"], preset["tech"])
    elif choice == "0":
        preset = characterPresets["testman"]
        return PlayerStats(preset["cooking"], preset["management"], preset["service"], preset["stamina"], preset["tech"])
    

characterPresets = {
    "chef": {
        "cooking": 16,
        "management": 8,
        "service": 12,
        "stamina": 10,
        "tech": 14
    },
    "businessman": {
        "cooking": 8,
        "management": 16,
        "service": 12,
        "stamina": 14,
        "tech": 10
    },
    "service_expert": {
        "cooking": 10,
        "management": 12,
        "service": 16,
        "stamina": 12,
        "tech": 8
    },
    "testman": {
        "cooking": 20,
        "management": 20,
        "service": 20,
        "stamina": 20,
        "tech": 20
    }
}


# 한 번만 실행되는 캐릭터 로딩
# playerStats = characterSelection()