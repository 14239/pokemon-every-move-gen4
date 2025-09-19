-- 포켓몬 플래티넘 원샷 올무브 챌린지 루아 스크립트
-- BizHawk용 - 표준 형식

-- 설정
local POLLING_INTERVAL = 60  -- 폴링 간격 (프레임)
local COMMAND_FILE = "lua_interface/command.txt"
local DISABLE_TOUCH = false  -- true로 설정하면 터치 입력을 비활성화

-- 포켓몬 플래티넘 메모리 주소
local FIRST_MOVE_SLOT = 0x2C6AEC  -- 첫 번째 기술 슬롯 직접 주소

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

-- 첫 번째 기술 슬롯 주소 가져오기 (직접 주소 사용)
function getFirstMoveSlotAddress()
    return FIRST_MOVE_SLOT
end

-- 터치 입력 함수
function touchScreen(x, y, frames)
    for i = 1, frames do
        local to_set = {}
        local to_set_axes = {}

        to_set["Touch"] = true
        to_set_axes["Touch X"] = x
        to_set_axes["Touch Y"] = y

        joypad.set(to_set)
        joypad.setanalog(to_set_axes)
        emu.frameadvance()
    end

    -- 터치 완전 해제
    client.clearautohold()
    for i = 1, 10 do
        emu.frameadvance()
    end
end

-- 기술 변경
function changeMove(moveIdStr)
    local moveSlotAddr = getFirstMoveSlotAddress()

    -- 문자열을 숫자로 변환
    local moveId = tonumber(moveIdStr)
    if not moveId then
        print("잘못된 기술 ID: " .. moveIdStr)
        return false
    end

    -- 기술 변경 (2바이트 리틀엔디안)
    memory.write_u16_le(moveSlotAddr, moveId, "Main RAM")
    print(string.format("기술 변경: %d (0x%04X)", moveId, moveId))

    -- 터치 입력이 비활성화되지 않은 경우에만 실행
    if not DISABLE_TOUCH then
        -- 0.5초 대기 후 좌측상단 두번 클릭 (30프레임 = 0.5초)
        for i = 1, 30 do
            emu.frameadvance()
        end

        -- 첫 번째 클릭 (좌측상단: 50, 50)
        touchScreen(50, 50, 5)

        -- 0.5초 대기
        for i = 1, 30 do
            emu.frameadvance()
        end

        -- 두 번째 클릭
        touchScreen(50, 50, 5)

        print("터치 입력 완료")
    else
        print("터치 입력 비활성화됨")
    end
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
    local moveAddr = getFirstMoveSlotAddress()
    local currentMove = memory.read_u16_le(moveAddr, "Main RAM")

    gui.text(10, 10, string.format("Move Slot Addr: 0x%08X", moveAddr))
    gui.text(10, 30, string.format("Current Move: %d (0x%04X)", currentMove, currentMove))

    -- 명령 대기 상태 표시
    if fileExists(COMMAND_FILE) then
        gui.text(10, 50, "Status: Command Pending")
    else
        gui.text(10, 50, "Status: Waiting for Command")
    end
end

-- 스크립트 시작
initialize()

-- BizHawk 메인 루프
while true do
    mainLoop()
    watchMemory()
    emu.frameadvance()
end