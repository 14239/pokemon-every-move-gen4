import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import json
import os
import time
from datetime import datetime
import configparser
import threading

class PokemonChallengeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("포켓몬 4세대 - 원샷 올무브 챌린지")
        self.root.geometry("800x600")

        # 데이터 초기화
        self.moves_df = None
        self.used_moves = [False] * 469
        self.move_history = []  # 사용한 기술 히스토리 [{"id": 1, "name": "몸통박치기", "timestamp": "2025-01-15 10:30:00"}, ...]
        self.current_save_file = None
        self.filtered_moves = None
        self.sort_column = None
        self.sort_reverse = False

        # 설정 로드
        self.load_settings()

        # 통신 파일 경로
        self.command_file = "lua_interface/command.txt"

        # UI 초기화
        self.setup_ui()

        # 데이터 로드
        self.load_moves_data()

        # 사용 가능한 기술 콤보박스 초기화
        self.update_available_moves_combo()

    def load_settings(self):
        """설정 파일 로드"""
        self.config = configparser.ConfigParser()
        if os.path.exists("settings.ini"):
            self.config.read("settings.ini", encoding='utf-8')
        else:
            # 기본 설정
            self.config['General'] = {
                'auto_save_interval': '600',
                'theme': 'default',
                'window_width': '800',
                'window_height': '600'
            }

    def setup_ui(self):
        """UI 구성 요소 설정"""
        # 메뉴바
        self.setup_menubar()

        # 상단 검색/필터 패널
        self.setup_search_panel()

        # 중앙 기술 리스트
        self.setup_moves_treeview()

        # 하단 통계 패널
        self.setup_stats_panel()

    def setup_menubar(self):
        """메뉴바 설정"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 파일 메뉴
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="파일", menu=file_menu)
        file_menu.add_command(label="새 챌린지", command=self.new_challenge)
        file_menu.add_command(label="챌린지 열기", command=self.load_challenge)
        file_menu.add_command(label="저장", command=self.save_challenge)
        file_menu.add_command(label="다른 이름으로 저장", command=self.save_challenge_as)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.root.quit)

        # 도구 메뉴
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="도구", menu=tools_menu)
        tools_menu.add_command(label="모든 기술 초기화", command=self.reset_all_moves)

    def setup_search_panel(self):
        """검색/필터 패널 설정"""
        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        # 검색 입력
        ttk.Label(search_frame, text="검색:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(5, 10))

        # 타입 필터
        ttk.Label(search_frame, text="타입:").pack(side=tk.LEFT)
        self.type_var = tk.StringVar(value="전체")
        type_combo = ttk.Combobox(search_frame, textvariable=self.type_var, width=10, state="readonly")
        type_combo['values'] = ("전체", "노말", "격투", "비행", "독", "땅", "바위", "벌레",
                               "고스트", "강철", "불꽃", "물", "풀", "전기", "에스퍼",
                               "얼음", "드래곤", "악")
        type_combo.pack(side=tk.LEFT, padx=(5, 10))
        type_combo.bind('<<ComboboxSelected>>', self.on_filter_change)

        # 상태 필터
        ttk.Label(search_frame, text="상태:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="전체")
        status_combo = ttk.Combobox(search_frame, textvariable=self.status_var, width=10, state="readonly")
        status_combo['values'] = ("전체", "사용됨", "사용안됨")
        status_combo.pack(side=tk.LEFT, padx=(5, 10))
        status_combo.bind('<<ComboboxSelected>>', self.on_filter_change)

        # 카테고리 필터
        ttk.Label(search_frame, text="카테고리:").pack(side=tk.LEFT)
        self.category_var = tk.StringVar(value="전체")
        category_combo = ttk.Combobox(search_frame, textvariable=self.category_var, width=10, state="readonly")
        category_combo['values'] = ("전체", "물리", "특수", "변화")
        category_combo.pack(side=tk.LEFT, padx=(5, 20))
        category_combo.bind('<<ComboboxSelected>>', self.on_filter_change)


    def setup_moves_treeview(self):
        """기술 리스트 Treeview 설정"""
        # 메인 프레임 (가로로 나누기)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 왼쪽 프레임 (기술 리스트)
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 오른쪽 프레임 (히스토리)
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Treeview (기술 리스트)
        columns = ("ID", "기술명", "타입", "카테고리", "위력", "명중률", "PP")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15)

        # 컬럼 설정 (정렬 가능)
        self.tree.heading("ID", text="ID", command=lambda: self.sort_treeview("id"))
        self.tree.heading("기술명", text="기술명", command=lambda: self.sort_treeview("name"))
        self.tree.heading("타입", text="타입", command=lambda: self.sort_treeview("type"))
        self.tree.heading("카테고리", text="카테고리", command=lambda: self.sort_treeview("category"))
        self.tree.heading("위력", text="위력", command=lambda: self.sort_treeview("power"))
        self.tree.heading("명중률", text="명중률", command=lambda: self.sort_treeview("accuracy"))
        self.tree.heading("PP", text="PP", command=lambda: self.sort_treeview("pp"))

        # 컬럼 너비 설정
        self.tree.column("ID", width=50)
        self.tree.column("기술명", width=120)
        self.tree.column("타입", width=70)
        self.tree.column("카테고리", width=70)
        self.tree.column("위력", width=50)
        self.tree.column("명중률", width=50)
        self.tree.column("PP", width=40)

        # 회색 태그 설정 (사용된 기술용)
        self.tree.tag_configure("used", foreground="gray")

        # 스크롤바 (기술 리스트)
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 패킹 (기술 리스트)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 트리뷰 선택 이벤트
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

        # 히스토리 섹션
        self.setup_history_panel(right_frame)

    def setup_history_panel(self, parent):
        """최근 기록 패널 설정"""
        # 기술 선택 섹션
        selection_frame = ttk.LabelFrame(parent, text="기술 선택", padding=10)
        selection_frame.pack(fill=tk.X, pady=(0, 10))

        # 기술 선택 콤보박스 (검색 가능)
        ttk.Label(selection_frame, text="기술:").pack(anchor=tk.W)
        self.move_selection_var = tk.StringVar()
        self.move_combo = ttk.Combobox(selection_frame, textvariable=self.move_selection_var,
                                      width=20, font=("맑은 고딕", 9))
        self.move_combo.pack(fill=tk.X, pady=(2, 5))
        self.move_combo.bind('<<ComboboxSelected>>', self.on_move_combo_select)
        self.move_combo.bind('<KeyRelease>', self.on_move_combo_search)

        # 기술 사용 버튼
        self.use_button = ttk.Button(selection_frame, text="기술 사용",
                                    command=self.on_use_button_click, width=15)
        self.use_button.pack(pady=(0, 5))

        # 히스토리 섹션
        history_label_frame = ttk.LabelFrame(parent, text="최근 기록", padding=5)
        history_label_frame.pack(fill=tk.BOTH, expand=True)

        # 히스토리 리스트박스
        history_frame = ttk.Frame(history_label_frame)
        history_frame.pack(fill=tk.BOTH, expand=True)

        self.history_listbox = tk.Listbox(history_frame, width=25, height=12, font=("맑은 고딕", 9))
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 히스토리 스크롤바
        history_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=history_scroll.set)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_stats_panel(self):
        """통계 패널 설정"""
        stats_frame = ttk.Frame(self.root)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        # 현재 세이브 파일 표시
        self.save_file_var = tk.StringVar(value="세이브 파일: 없음")
        ttk.Label(stats_frame, textvariable=self.save_file_var).pack(side=tk.LEFT)

        # 사용한 기술 수 표시
        self.progress_var = tk.StringVar(value="사용한 기술: 0/469 (0.0%)")
        ttk.Label(stats_frame, textvariable=self.progress_var).pack(side=tk.RIGHT)

    def load_moves_data(self):
        """포켓몬 기술 데이터 로드"""
        try:
            # CSV 로드
            self.moves_df = pd.read_csv("pokemon_moves.csv", dtype=str)

            # 숫자 컬럼들을 적절히 처리 (특수문자는 원본 유지)
            for col in ['power', 'pp']:
                # 숫자로 변환 가능한 것만 변환, 나머지는 원본 유지
                self.moves_df[col] = self.moves_df[col].apply(self.convert_to_numeric_if_possible)

            # accuracy는 %를 제거하고 숫자만 추출
            self.moves_df['accuracy_display'] = self.moves_df['accuracy']  # 원본 보관
            self.moves_df['accuracy'] = self.moves_df['accuracy'].apply(self.extract_accuracy_number)

            self.refresh_treeview()
            self.update_stats()
        except FileNotFoundError:
            messagebox.showerror("오류", "pokemon_moves.csv 파일을 찾을 수 없습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"데이터 로드 중 오류 발생: {str(e)}")

    def convert_to_numeric_if_possible(self, value):
        """가능하면 숫자로 변환, 불가능하면 원본 문자열 반환"""
        try:
            # 숫자만 있는 경우 int로 변환
            if str(value).isdigit():
                return int(value)
            else:
                return value  # "—", "∞" 등은 원본 유지
        except:
            return value

    def extract_accuracy_number(self, value):
        """명중률에서 숫자만 추출 (정렬용)"""
        try:
            if '%' in str(value):
                # "100%", "85%" 등에서 숫자만 추출
                num_str = str(value).replace('%', '')
                if num_str.isdigit():
                    return int(num_str)
            elif str(value) == '∞':
                return 999  # 무한대는 가장 큰 값으로
            elif str(value) == '—':
                return -1   # 없음은 가장 작은 값으로
            return value
        except:
            return value

    def refresh_treeview(self):
        """Treeview 새로고침"""
        if self.moves_df is None:
            return

        # 기존 항목 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 필터링된 데이터 가져오기
        filtered_df = self.get_filtered_moves()

        # 데이터 추가
        for _, row in filtered_df.iterrows():
            move_id = int(row['id'])

            item = self.tree.insert("", tk.END, values=(
                row['id'], row['name'], row['type'], row['category'],
                row['power'], row['accuracy_display'], row['pp']
            ))

            # 사용된 기술은 회색으로 표시
            if self.used_moves[move_id - 1]:
                self.tree.item(item, tags="used")

    def get_filtered_moves(self):
        """필터링된 기술 목록 반환"""
        if self.moves_df is None:
            return pd.DataFrame()

        df = self.moves_df.copy()

        # 검색어 필터
        search_text = self.search_var.get().strip()
        if search_text:
            df = df[df['name'].str.contains(search_text, case=False, na=False)]

        # 타입 필터
        if self.type_var.get() != "전체":
            df = df[df['type'] == self.type_var.get()]

        # 카테고리 필터
        if self.category_var.get() != "전체":
            df = df[df['category'] == self.category_var.get()]

        # 상태 필터
        if self.status_var.get() == "사용됨":
            df = df[df['id'].apply(lambda x: self.used_moves[int(x) - 1])]
        elif self.status_var.get() == "사용안됨":
            df = df[df['id'].apply(lambda x: not self.used_moves[int(x) - 1])]

        # 정렬 적용
        if self.sort_column:
            # 숫자 컬럼들은 이미 적절히 변환되어 있음
            if self.sort_column in ['id', 'power', 'accuracy', 'pp']:
                df[self.sort_column] = pd.to_numeric(df[self.sort_column], errors='coerce')

            df = df.sort_values(by=self.sort_column, ascending=not self.sort_reverse)

        return df

    def on_search_change(self, *args):
        """검색어 변경 시 호출"""
        self.refresh_treeview()

    def on_filter_change(self, event):
        """필터 변경 시 호출"""
        self.refresh_treeview()

    def sort_treeview(self, column):
        """Treeview 정렬"""
        # 같은 컬럼을 다시 클릭하면 역순으로
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        # 헤더에 정렬 방향 표시
        for col in ["id", "name", "type", "category", "power", "accuracy", "pp"]:
            heading_text = {
                "id": "ID", "name": "기술명", "type": "타입", "category": "카테고리",
                "power": "위력", "accuracy": "명중률", "pp": "PP"
            }[col]

            if col == column:
                arrow = " ↓" if self.sort_reverse else " ↑"
                self.tree.heading(heading_text, text=heading_text + arrow)
            else:
                self.tree.heading(heading_text, text=heading_text)

        self.refresh_treeview()

    def on_use_button_click(self):
        """사용 버튼 클릭 시 호출"""
        selected_text = self.move_selection_var.get().strip()
        if not selected_text:
            messagebox.showwarning("선택 오류", "사용할 기술을 선택해주세요.")
            return

        # "ID. 기술명" 형식에서 ID 추출
        try:
            move_id = int(selected_text.split('.')[0])
        except (ValueError, IndexError):
            messagebox.showwarning("선택 오류", "올바른 기술을 선택해주세요.")
            return

        # 이미 사용된 기술인지 확인
        if self.used_moves[move_id - 1]:
            messagebox.showwarning("경고", "이미 사용된 기술입니다.")
            return

        # 바로 사용 (확인창 없음)
        self.use_move(move_id)

    def use_move(self, move_id):
        """기술 사용 처리"""
        # 기술명 가져오기
        move_name = self.moves_df[self.moves_df['id'] == str(move_id)]['name'].iloc[0]

        # 기술 사용 표시
        self.used_moves[move_id - 1] = True

        # 히스토리에 추가
        self.add_to_history(move_id, move_name)

        # 루아 스크립트에 기술 ID 전송
        self.send_command_to_lua(str(move_id))

        # UI 업데이트
        self.refresh_treeview()
        self.update_stats()
        self.update_available_moves_combo()  # 콤보박스 업데이트
        self.move_selection_var.set("")  # 선택 초기화

    def send_command_to_lua(self, move_id):
        """루아 스크립트에 기술 ID 전송"""
        try:
            os.makedirs("lua_interface", exist_ok=True)
            with open(self.command_file, 'w', encoding='utf-8') as f:
                f.write(move_id)
            print(f"루아에 기술 ID 전송: {move_id}")
        except Exception as e:
            print(f"명령 전송 오류: {e}")

    def update_stats(self):
        """통계 정보 업데이트"""
        used_count = sum(self.used_moves)
        percentage = (used_count / 469) * 100
        self.progress_var.set(f"사용한 기술: {used_count}/469 ({percentage:.1f}%)")

    def update_history_display(self):
        """히스토리 리스트박스 업데이트"""
        self.history_listbox.delete(0, tk.END)

        # 최신 순으로 표시 (최근 것이 위에)
        total_count = len(self.move_history)
        recent_history = self.move_history[-50:] if len(self.move_history) > 50 else self.move_history

        for i, record in enumerate(reversed(recent_history)):
            # 전체 순서에서의 번호 계산 (최신이 위에 오도록)
            order_num = total_count - i
            display_text = f"{order_num}. {record['name']}"
            self.history_listbox.insert(tk.END, display_text)

    def add_to_history(self, move_id, move_name):
        """히스토리에 기술 사용 기록 추가"""
        from datetime import datetime

        record = {
            "id": move_id,
            "name": move_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.move_history.append(record)
        self.update_history_display()

    def update_available_moves_combo(self):
        """사용 가능한 기술들로 콤보박스 업데이트"""
        if self.moves_df is None:
            return

        # 사용 가능한 기술들만 필터링
        available_moves = []
        for _, row in self.moves_df.iterrows():
            move_id = int(row['id'])
            if not self.used_moves[move_id - 1]:  # 사용되지 않은 기술만
                move_text = f"{row['id']}. {row['name']}"
                available_moves.append(move_text)

        self.move_combo['values'] = available_moves

    def on_tree_select(self, event):
        """트리뷰에서 기술 선택 시 콤보박스에 반영"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.tree.item(item, "values")
        move_id = int(values[0])
        move_name = values[1]

        # 사용 가능한 기술인지 확인
        if not self.used_moves[move_id - 1]:
            move_text = f"{move_id}. {move_name}"
            self.move_selection_var.set(move_text)

    def on_move_combo_select(self, event):
        """콤보박스에서 기술 선택 시"""
        pass  # 선택만 하면 됨

    def on_move_combo_search(self, event):
        """콤보박스에서 검색 입력 시"""
        if self.moves_df is None:
            return

        search_text = self.move_selection_var.get().lower()
        if not search_text:
            self.update_available_moves_combo()
            return

        # 검색어로 필터링
        filtered_moves = []
        for _, row in self.moves_df.iterrows():
            move_id = int(row['id'])
            if not self.used_moves[move_id - 1]:  # 사용되지 않은 기술만
                move_name = row['name'].lower()
                if search_text in move_name or search_text in str(move_id):
                    move_text = f"{row['id']}. {row['name']}"
                    filtered_moves.append(move_text)

        self.move_combo['values'] = filtered_moves

    def new_challenge(self):
        """새 챌린지 시작"""
        if messagebox.askyesno("새 챌린지", "현재 진행 상황이 초기화됩니다. 계속하시겠습니까?"):
            self.used_moves = [False] * 469
            self.move_history.clear()
            self.current_save_file = None
            self.refresh_treeview()
            self.update_stats()
            self.update_history_display()
            self.update_available_moves_combo()
            self.move_selection_var.set("")
            self.save_file_var.set("세이브 파일: 없음")

    def load_challenge(self):
        """챌린지 로드"""
        file_path = filedialog.askopenfilename(
            title="챌린지 파일 열기",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="saves"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.used_moves = data.get('used_moves', [False] * 469)
                self.move_history = data.get('move_history', [])
                self.current_save_file = file_path

                self.refresh_treeview()
                self.update_stats()
                self.update_history_display()
                self.update_available_moves_combo()
                self.move_selection_var.set("")
                self.save_file_var.set(f"세이브 파일: {os.path.basename(file_path)}")

                messagebox.showinfo("성공", "챌린지를 성공적으로 로드했습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"파일 로드 중 오류 발생: {str(e)}")

    def save_challenge(self):
        """챌린지 저장"""
        if not self.current_save_file:
            self.save_challenge_as()
        else:
            self._save_to_file(self.current_save_file)

    def save_challenge_as(self):
        """다른 이름으로 챌린지 저장"""
        file_path = filedialog.asksaveasfilename(
            title="챌린지 파일 저장",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="saves"
        )

        if file_path:
            self.current_save_file = file_path
            self._save_to_file(file_path)

    def _save_to_file(self, file_path):
        """파일에 저장"""
        try:
            os.makedirs("saves", exist_ok=True)

            save_data = {
                "save_name": os.path.basename(file_path),
                "created_date": datetime.now().isoformat(),
                "used_moves": self.used_moves,
                "move_history": self.move_history,
                "metadata": {
                    "game_version": "Platinum",
                    "challenge_type": "Single Use",
                    "total_moves": 469,
                    "used_count": sum(self.used_moves)
                }
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)

            self.save_file_var.set(f"세이브 파일: {os.path.basename(file_path)}")
            print(f"챌린지 저장 완료: {file_path}")
        except Exception as e:
            messagebox.showerror("오류", f"파일 저장 중 오류 발생: {str(e)}")

    def reset_all_moves(self):
        """모든 기술 초기화"""
        if messagebox.askyesno("초기화", "모든 기술을 사용 안함 상태로 초기화하시겠습니까?"):
            self.used_moves = [False] * 469
            self.move_history.clear()
            self.refresh_treeview()
            self.update_stats()
            self.update_history_display()
            self.update_available_moves_combo()
            self.move_selection_var.set("")


def main():
    root = tk.Tk()
    app = PokemonChallengeGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()