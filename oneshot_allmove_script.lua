-- 포켓몬 플래티넘 원샷 올무브 챌린지 루아 스크립트
-- DeSmuME용 - 표준 형식

-- 설정
local POLLING_INTERVAL = 60  -- 폴링 간격 (프레임)
local COMMAND_FILE = "lua_interface/command.txt"

-- 포켓몬 플래티넘 메모리 주소
local PARTY_POKEMON_BASE = 0x02101D2C  -- 포인터 체인 시작점
local MOVE_DATA_OFFSET = 0x29C         -- 기술 데이터 오프셋

-- 전역 변수
local frameCounter = 0

-- 유틸리티 함수들
function fileExists(filename)
    local file = io.open(filename, "r")
    if file then
        file:close()
        return true
    end
    return nil
end

function readFile(filename)
    local file = io.open(filename, "r")
    if file then
        local content = file:read("*all")
        file:close()
        return content
    end
    return nil
end

function deleteFile(filename)
    os.remove(filename)
end

-- 동적 메모리 주소 탐지
function findPartyPokemonAddress()
    -- 포인터 체인을 따라 실제 포켓몬 데이터 주소 찾기
    local basePointer = memory.read_u32_le(PARTY_POKEMON_BASE)
    if basePointer and basePointer > 0x02000000 then
        return basePointer
    end
    return nil
end

-- 현재 첫 번째 포켓몬의 첫 번째 기술 슬롯 주소 가져오기
function getFirstMoveSlotAddress()
    local partyBase = findPartyPokemonAddress()
    if not partyBase then
        return nil
    end

    -- 첫 번째 포켓몬의 첫 번째 기술 슬롯
    return partyBase + MOVE_DATA_OFFSET
end

-- 기술 변경
function changeMove(moveIdStr)
    local moveSlotAddr = getFirstMoveSlotAddress()
    if not moveSlotAddr then
        print("포켓몬 데이터 주소를 찾을 수 없습니다")
        return false
    end

    -- 문자열을 숫자로 변환
    local moveId = tonumber(moveIdStr)
    if not moveId then
        print("잘못된 기술 ID: " .. moveIdStr)
        return false
    end

    -- 기술 변경
    memory.write_u16_le(moveSlotAddr, moveId)
    print(string.format("기술 변경: %d", moveId))
    return true
end

-- 명령 확인 및 처리
function checkCommands()
    if fileExists(COMMAND_FILE) then
        local moveId = readFile(COMMAND_FILE)
        if moveId and moveId:len() > 0 then
            -- 개행문자 제거
            moveId = moveId:gsub("[\r\n]", "")

            -- 기술 변경 실행
            if changeMove(moveId) then
                print("기술 변경 완료: " .. moveId)
            else
                print("기술 변경 실패: " .. moveId)
            end

            -- 명령 파일 삭제
            deleteFile(COMMAND_FILE)
        end
    end
end

-- 메인 폴링 함수
function mainLoop()
    frameCounter = frameCounter + 1

    if frameCounter % POLLING_INTERVAL == 0 then
        checkCommands()
    end
end

-- 초기화
function initialize()
    print("포켓몬 플래티넘 원샷 올무브 챌린지 스크립트 시작")
    print("첫 번째 포켓몬의 첫 번째 기술 슬롯을 변경합니다")

    -- 디렉토리 생성
    os.execute("mkdir lua_interface 2>nul")

    print("초기화 완료 - 명령 대기 중...")
end

-- 메모리 워치 함수 (디버깅용)
function watchMemory()
    local partyBase = findPartyPokemonAddress()
    if partyBase then
        gui.text(10, 10, string.format("Party Base: 0x%08X", partyBase))

        -- 첫 번째 포켓몬의 첫 번째 기술 표시
        local moveAddr = getFirstMoveSlotAddress()
        if moveAddr then
            local currentMove = memory.read_u16_le(moveAddr)
            gui.text(10, 30, string.format("Current Move: %d (0x%04X)", currentMove, currentMove))
            gui.text(10, 50, string.format("Move Slot Addr: 0x%08X", moveAddr))
        end
    else
        gui.text(10, 10, "Party Base: Not Found")
    end

    -- 명령 대기 상태 표시
    if fileExists(COMMAND_FILE) then
        gui.text(10, 70, "Status: Command Pending")
    else
        gui.text(10, 70, "Status: Waiting for Command")
    end
end

-- 스크립트 시작
initialize()

-- DeSmuME 메인 루프
while true do
    mainLoop()
    watchMemory()
    emu.frameadvance()
end