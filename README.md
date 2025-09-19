# 포켓몬 플래티넘 원샷 올무브 챌린지 도구

포켓몬 플래티넘에서 469개의 모든 기술을 각각 한 번씩만 사용할 수 있는 챌린지를 위한 도구입니다.

## 시스템 구조

```
[Python GUI 프로그램] ←→ [파일 통신] ←→ [DeSmuME 루아 스크립트] ←→ [포켓몬 게임]
```

## 작동 방식

1. **Python GUI에서 기술 선택** → 기술 ID 전송
2. **루아 스크립트로 기술 ID 전송** → command.txt 파일을 통해
3. **루아가 첫 번째 포켓몬의 첫 번째 기술 슬롯을 변경** → 받은 기술 ID로
4. **Python GUI에서 해당 기술을 사용됨 처리** → 다음부터 사용 불가

## 파일 구조

```
pokemon-every-move-pt/
├── oneshot_allmove_challenge.py  # Python GUI 프로그램
├── pokemon_moves.csv             # 469개 기술 마스터 데이터 (한글명)
├── oneshot_allmove_script.lua    # DeSmuME 루아 스크립트
├── settings.ini                  # 앱 설정
├── build_release.bat             # 실행파일 빌드 스크립트
├── lua_interface/                # 루아 통신 폴더
│   └── command.txt              # Python → 루아 기술 ID 전송
├── saves/                       # 챌린지 세이브 파일들
│   └── example_challenge.json
└── README.md                    # 이 파일
```

## 설치 및 실행

### 필요 요구사항

- Python 3.8+
- pandas, tkinter (보통 Python에 기본 포함)
- DeSmuME 에뮬레이터
- 포켓몬 플래티넘 ROM

### Python 패키지 설치

```bash
pip install pandas
```

### 실행 방법

#### 옵션 1: 실행 파일 사용 (권장)
1. **빌드 실행**
   ```bash
   build_release.bat
   ```
2. **실행 파일 실행**
   - `release/oneshot_allmove_challenge.exe` 실행

#### 옵션 2: Python 직접 실행
1. **Python GUI 프로그램 실행**
   ```bash
   python oneshot_allmove_challenge.py
   ```

#### DeSmuME 설정
1. **DeSmuME에서 루아 스크립트 로드**
   - DeSmuME 실행
   - Tools → Lua Scripting → New Lua Script Window
   - `oneshot_allmove_script.lua` 파일 로드

2. **포켓몬 플래티넘 게임 시작**
   - ROM을 로드하고 게임 시작
   - 루아 스크립트가 자동으로 기술 변경 처리

## 사용법

### GUI 프로그램 기능

1. **기술 리스트**
   - 469개 모든 기술이 한글명으로 표시됩니다
   - 사용된 기술은 회색으로 표시됩니다
   - 클릭으로 기술 선택 가능

2. **기술 선택 패널**
   - 검색 가능한 콤보박스로 기술 선택
   - 선택한 기술을 "기술 사용" 버튼으로 즉시 사용
   - 사용된 기술은 목록에서 제외

3. **검색 및 필터**
   - 기술명으로 실시간 검색
   - 타입별 필터 (노말, 격투, 비행 등)
   - 상태별 필터 (전체, 사용됨, 사용안됨)
   - 카테고리별 필터 (물리, 특수, 변화)

4. **히스토리 및 통계**
   - 사용한 기술 순서대로 히스토리 표시
   - 실시간 사용률 통계 (X/469개 사용)

5. **파일 관리**
   - 새 챌린지: 모든 기술 초기화
   - 챌린지 열기: 저장된 진행상황 로드
   - 저장: 현재 진행상황 저장 (수동 저장만 지원)
   - 다른 이름으로 저장: 새 파일로 저장

6. **도구**
   - 모든 기술 초기화

### 루아 스크립트 기능

1. **기술 변경**
   - Python에서 선택한 기술을 첫 번째 포켓몬의 첫 번째 기술 슬롯에 설정
   - 실시간으로 파일 명령을 감지하여 처리

2. **파일 통신**
   - Python 프로그램과 command.txt 파일을 통해 통신
   - 60프레임마다 명령 확인 및 처리

3. **디버깅 정보**
   - 화면에 현재 기술 정보 표시
   - 콘솔에 기술 변경 로그 출력

## 통신 프로토콜

### 기술 변경 처리

1. **Python → Lua**
   ```
   command.txt: "329"
   (기술 ID를 10진수 문자열로 전송)
   ```

2. **Lua 처리**
   - 기술 ID를 숫자로 변환 ("329" → 329)
   - DeSmuME가 329를 16진수(0x0149)로 변환하여 메모리에 저장
   - 첫 번째 포켓몬의 첫 번째 기술 슬롯이 329번 기술로 변경됨
   - command.txt 파일 삭제

## 세이브 파일 형식

```json
{
  "save_name": "example_challenge.json",
  "created_date": "2025-09-19T16:57:55.429352",
  "used_moves": [false, true, false, ...], // 469개 불린 배열
  "move_history": [
    {
      "id": 8,
      "name": "냉동펀치",
      "timestamp": "2025-09-19 16:53:36"
    }
  ],
  "metadata": {
    "game_version": "Platinum",
    "challenge_type": "Single Use",
    "total_moves": 469,
    "used_count": 6
  }
}
```

## 주의사항

1. **메모리 주소**
   - 루아 스크립트의 메모리 주소는 ROM 버전에 따라 다를 수 있습니다
   - 필요시 `oneshot_allmove_script.lua`의 주소를 수정하세요

2. **파일 권한**
   - `lua_interface/` 폴더의 읽기/쓰기 권한이 필요합니다
   - Windows에서는 관리자 권한이 필요할 수 있습니다

3. **동기화**
   - Python 프로그램과 루아 스크립트를 동시에 실행해야 합니다
   - 파일 기반 통신이므로 약간의 지연이 있을 수 있습니다

## 문제해결

### 일반적인 문제

1. **"pokemon_moves.csv 파일을 찾을 수 없습니다"**
   - CSV 파일이 올바른 위치에 있는지 확인
   - 파일 경로에 한글이 있으면 영문 경로로 변경

2. **루아 스크립트가 작동하지 않음**
   - DeSmuME에서 루아 스크립트가 정상 로드되었는지 확인
   - 콘솔 창에서 오류 메시지 확인
   - 메모리 주소가 올바른지 확인

3. **통신이 안됨**
   - `lua_interface/` 폴더가 존재하는지 확인
   - 파일 권한 확인
   - 방화벽/백신 프로그램 확인

### 디버깅

1. **Python 프로그램**
   - 콘솔에서 실행하여 오류 메시지 확인
   - `settings.ini` 파일의 설정 확인

2. **루아 스크립트**
   - DeSmuME 콘솔 창에서 로그 확인
   - 메모리 워치 기능으로 주소 확인

## 개발 정보

- **언어**: Python 3.8+, Lua 5.1
- **GUI**: Tkinter
- **데이터**: pandas, JSON
- **에뮬레이터**: DeSmuME
- **게임**: 포켓몬 플래티넘

## 라이선스

이 프로젝트는 교육 및 개인 사용 목적으로 제작되었습니다.