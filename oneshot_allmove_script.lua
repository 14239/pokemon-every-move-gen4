-- 포켓몬 4세대 원샷 올무브 챌린지 루아 스크립트 (동적 메모리 주소)
-- BizHawk용 - 메모리 스캔 기능 포함

-- 설정
local POLLING_INTERVAL = 60  -- 폴링 간격 (프레임)
local COMMAND_FILE = "lua_interface/command.txt"
local RESULT_FILE = "lua_interface/result.txt"
local MEMORY_CONFIG_FILE = "lua_interface/memory_config.txt"
local DISABLE_TOUCH = false  -- true로 설정하면 터치 입력을 비활성화

-- 메모리 스캔 범위
local SCAN_RANGE_START = 0x2C6000  -- 스캔 시작 주소
local SCAN_RANGE_END = 0x2C6B00    -- 스캔 종료 주소

-- 메모리 주소 (초기값 - 설정 파일에서 로드됨)
local FIRST_MOVE_SLOT_1P = 0x2C6AEC  -- 1P 첫 번째 기술 슬롯 주소
local FIRST_MOVE_SLOT_2P = 0x2C6C6C  -- 2P 첫 번째 기술 슬롯 주소

-- 전역 변수
local frameCounter = 0
local addressConfigLoaded = false

-- ========================================
-- 유틸리티 함수들
-- ========================================

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

function writeFile(filename, content)
	local file = io.open(filename, "w")
	if file then
		file:write(content)
		file:close()
		return true
	end
	return false
end

function deleteFile(filename)
	os.remove(filename)
end

-- ========================================
-- 메모리 설정 관리
-- ========================================

function loadMemoryConfig()
	if fileExists(MEMORY_CONFIG_FILE) then
		local config = readFile(MEMORY_CONFIG_FILE)
		if config then
			-- 개행문자 제거
			config = config:gsub("[\r\n]", "")

			-- 16진수 문자열을 숫자로 변환
			local addr = tonumber(config, 16)
			if addr and addr > 0 then
				FIRST_MOVE_SLOT_1P = addr
				FIRST_MOVE_SLOT_2P = addr + 0x180  -- 2P는 1P에서 0x180 떨어진 위치
				addressConfigLoaded = true
				print(string.format("메모리 설정 로드: 1P=0x%08X, 2P=0x%08X", FIRST_MOVE_SLOT_1P, FIRST_MOVE_SLOT_2P))
				return true
			end
		end
	end
	print("메모리 설정 파일 없음 - 기본값 사용")
	return false
end

function saveMemoryConfig(address)
	local config = string.format("0x%08X", address)
	if writeFile(MEMORY_CONFIG_FILE, config) then
		print("메모리 설정 저장: " .. config)
		return true
	end
	return false
end

-- ========================================
-- 메모리 스캔 함수
-- ========================================

function scanMemoryForMoves(move1, move2, move3, move4)
	print("==============================================")
	print("메모리 스캔 시작")
	print(string.format("검색 패턴: %d, %d, %d, %d", move1, move2, move3, move4))
	print(string.format("스캔 범위: 0x%08X - 0x%08X", SCAN_RANGE_START, SCAN_RANGE_END))

	local foundCount = 0
	local foundAddr = nil

	-- 범위 스캔 (2바이트씩)
	for addr = SCAN_RANGE_START, SCAN_RANGE_END - 8, 2 do
		local m1 = memory.read_u16_le(addr, "Main RAM")
		local m2 = memory.read_u16_le(addr + 2, "Main RAM")
		local m3 = memory.read_u16_le(addr + 4, "Main RAM")
		local m4 = memory.read_u16_le(addr + 6, "Main RAM")

		if m1 == move1 and m2 == move2 and m3 == move3 and m4 == move4 then
			foundCount = foundCount + 1
			if foundAddr == nil then
				foundAddr = addr
			end
			print(string.format("패턴 발견 #%d: 0x%08X", foundCount, addr))
		end
	end

	-- 결과 처리
	if foundAddr then
		local result = string.format("0x%08X", foundAddr)
		writeFile(RESULT_FILE, result)
		print(string.format("주소 발견 완료: %s (총 %d개 발견)", result, foundCount))

		-- 설정 저장
		saveMemoryConfig(foundAddr)
		FIRST_MOVE_SLOT_1P = foundAddr
		FIRST_MOVE_SLOT_2P = foundAddr + 0x180
		addressConfigLoaded = true

		print("==============================================")
		return true
	else
		writeFile(RESULT_FILE, "ERROR:NOT_FOUND")
		print("오류: 일치하는 패턴을 찾을 수 없습니다")
		print("==============================================")
		return false
	end
end

-- ========================================
-- 게임 기능
-- ========================================

function getFirstMoveSlotAddress(player)
	if player == 2 then
		return FIRST_MOVE_SLOT_2P
	else
		return FIRST_MOVE_SLOT_1P
	end
end

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

function changeMove(player, moveIdStr)
	local moveSlotAddr = getFirstMoveSlotAddress(player)

	-- 문자열을 숫자로 변환
	local moveId = tonumber(moveIdStr)
	if not moveId then
		print("잘못된 기술 ID: " .. moveIdStr)
		return false
	end

	-- 기술 변경 (2바이트 리틀엔디안)
	memory.write_u16_le(moveSlotAddr, moveId, "Main RAM")
	print(string.format("%dP 기술 변경: %d (0x%04X) at 0x%08X", player, moveId, moveId, moveSlotAddr))

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

-- ========================================
-- 명령 처리
-- ========================================

function checkCommands()
	if fileExists(COMMAND_FILE) then
		local command = readFile(COMMAND_FILE)
		if command and command:len() > 0 then
			-- 개행문자 제거
			command = command:gsub("[\r\n]", "")

			-- SCAN 명령 처리: "SCAN:ID1,ID2,ID3,ID4"
			if command:match("^SCAN:") then
				local moves = {}
				for id in command:gmatch("%d+") do
					table.insert(moves, tonumber(id))
				end

				if #moves == 4 then
					scanMemoryForMoves(moves[1], moves[2], moves[3], moves[4])
				else
					print("오류: SCAN 명령 형식이 잘못되었습니다")
					writeFile(RESULT_FILE, "ERROR:INVALID_FORMAT")
				end

			-- 기존 기술 변경 명령: "1P:123" 또는 "2P:456"
			elseif command:match("^%d+P:%d+$") then
				local player, moveId = command:match("(%d+)P:(%d+)")

				if player and moveId then
					player = tonumber(player)
					if changeMove(player, moveId) then
						print(string.format("%dP 기술 변경 완료: %s", player, moveId))
					else
						print(string.format("%dP 기술 변경 실패: %s", player, moveId))
					end
				end

			else
				print("잘못된 명령 형식: " .. command)
			end

			-- 명령 파일 삭제
			deleteFile(COMMAND_FILE)
		end
	end
end

function mainLoop()
	frameCounter = frameCounter + 1

	if frameCounter % POLLING_INTERVAL == 0 then
		checkCommands()
	end
end

-- ========================================
-- 초기화 및 UI
-- ========================================

function initialize()
	print("==============================================")
	print("포켓몬 4세대 원샷 올무브 챌린지 스크립트")
	print("동적 메모리 주소 지원 버전")
	print("==============================================")

	-- 디렉토리 생성
	os.execute("mkdir lua_interface 2>nul")

	-- 메모리 설정 로드
	loadMemoryConfig()

	print("첫 번째 포켓몬의 첫 번째 기술 슬롯을 변경합니다")
	print("초기화 완료 - 명령 대기 중...")
	print("==============================================")
end

function watchMemory()
	local moveAddr1P = getFirstMoveSlotAddress(1)
	local moveAddr2P = getFirstMoveSlotAddress(2)
	local currentMove1P = memory.read_u16_le(moveAddr1P, "Main RAM")
	local currentMove2P = memory.read_u16_le(moveAddr2P, "Main RAM")

	local y = 10

	-- 설정 상태 표시
	if addressConfigLoaded then
		gui.text(10, y, "Memory Config: Loaded", "lime")
	else
		gui.text(10, y, "Memory Config: Default", "yellow")
	end
	y = y + 20

	gui.text(10, y, string.format("1P Move Addr: 0x%08X", moveAddr1P), "white")
	y = y + 20
	gui.text(10, y, string.format("1P Current Move: %d (0x%04X)", currentMove1P, currentMove1P), "white")
	y = y + 20
	gui.text(10, y, string.format("2P Move Addr: 0x%08X", moveAddr2P), "white")
	y = y + 20
	gui.text(10, y, string.format("2P Current Move: %d (0x%04X)", currentMove2P, currentMove2P), "white")
	y = y + 20

	-- 명령 대기 상태 표시
	if fileExists(COMMAND_FILE) then
		gui.text(10, y, "Status: Command Pending", "green")
	else
		gui.text(10, y, "Status: Waiting for Command", "white")
	end
end

-- ========================================
-- 스크립트 시작
-- ========================================

initialize()

-- BizHawk 메인 루프
while true do
	mainLoop()
	watchMemory()
	emu.frameadvance()
end
