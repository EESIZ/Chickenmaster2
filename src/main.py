"""
메인 게임 루프 및 흐름 제어 모듈
"""
from game.characterSelect import characterSelection

def select_game_mode():
    """게임 모드를 선택하는 메뉴를 표시하고 사용자 입력을 받습니다."""
    while True:
        print("\n===== 게임 모드 선택 =====")
        print("1. 새 게임")
        print("2. 불러오기 (미구현)")
        print("3. 종료")
        
        choice = input("선택: ")
        
        if choice == "1":
            print("\n새 게임을 시작합니다.")
            player_stats = characterSelection()
            print(f"\n선택한 캐릭터의 스탯: {player_stats}")
            # 여기서부터 실제 게임 플레이 로직이 시작됩니다.
            # 지금은 스탯 확인 후 다시 메인 메뉴로 돌아갑니다.
        elif choice == "2":
            print("\n아직 지원되지 않는 기능입니다.")
        elif choice == "3":
            print("\n게임을 종료합니다.")
            return # 루프를 종료하고 main 함수로 돌아가 프로그램 종료
        else:
            print("\n잘못된 선택입니다. 다시 입력해주세요.")

def main():
    """게임의 메인 진입점입니다."""
    print("치킨마스터2에 오신 것을 환영합니다!")
    select_game_mode()

if __name__ == "__main__":
    main() 