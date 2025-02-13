import os
import pandas as pd
import glob
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from threading import Thread
import subprocess
import platform

class EyeDataProcessor:
    def __init__(self, root):
        self.root = root
        self.root.title("Eye Data Processor")
        self.root.geometry("600x400")
        
        # GUI 구성요소 생성
        self.create_widgets()
        
    def create_widgets(self):
        # 상단 프레임
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        # 폴더 선택 버튼
        self.select_btn = ttk.Button(top_frame, text="House 폴더 선택", command=self.select_folder)
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        # 처리 시작 버튼
        self.process_btn = ttk.Button(top_frame, text="처리 시작", command=self.start_processing)
        self.process_btn.pack(side=tk.LEFT, padx=5)
        self.process_btn['state'] = 'disabled'
        
        # 상태 레이블
        self.status_label = ttk.Label(top_frame, text="House 폴더를 선택해주세요")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 로그 창
        self.log_area = scrolledtext.ScrolledText(self.root, height=15, width=70)
        self.log_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 진행바
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        
    def select_folder(self):
        folder_path = filedialog.askdirectory(title="House 폴더 선택")
        if folder_path:
            folder_name = os.path.basename(folder_path)
            if folder_name == "House":
                os.chdir(os.path.dirname(folder_path))
                self.status_label['text'] = f"선택된 폴더: {folder_path}"
                self.process_btn['state'] = 'normal'
                self.log_message(f"House 폴더가 선택되었습니다: {folder_path}")
            else:
                self.status_label['text'] = "올바른 폴더가 아닙니다. House 폴더를 선택해주세요."
                self.process_btn['state'] = 'disabled'
    
    def log_message(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
    
    def start_processing(self):
        self.process_btn['state'] = 'disabled'
        self.select_btn['state'] = 'disabled'
        self.progress.start()
        
        # 별도 스레드에서 처리
        thread = Thread(target=self.process_data)
        thread.daemon = True
        thread.start()
    
    def process_data(self):
        try:
            self.log_message("데이터 처리를 시작합니다...")
            
            final_df = pd.DataFrame()
            participant_folders = glob.glob('House/*')
            
            def get_folder_number(folder_path):
                folder_name = os.path.basename(folder_path)
                number = ''.join(filter(str.isdigit, folder_name.split()[0]))
                return int(number) if number else 0
            
            participant_folders.sort(key=get_folder_number)
            
            for participant_path in participant_folders:
                participant_num = os.path.basename(participant_path)
                
                if '(eyedata 없음)' in participant_path:
                    self.log_message(f"참가자 {participant_num}: eyedata 없음 - 건너뛰기")
                    continue
                
                self.log_message(f"참가자 {participant_num} 데이터 처리 중...")
                
                eye_folder = os.path.join(participant_path, 'Eye')
                if not os.path.exists(eye_folder):
                    self.log_message(f"Warning: Eye 폴더를 찾을 수 없습니다 - {eye_folder}")
                    continue
                
                eye_files = glob.glob(os.path.join(eye_folder, 'EyeData*_sequence_result.xlsx'))
                
                if not eye_files:
                    self.log_message(f"Warning: EyeData 파일을 찾을 수 없습니다 - {eye_folder}")
                    continue
                
                for eye_file in eye_files:
                    try:
                        self.log_message(f"처리 중인 파일: {os.path.basename(eye_file)}")
                        env_num = ''.join(filter(str.isdigit, 
                            os.path.basename(eye_file).split('EyeData')[1].split('_')[0]))
                        
                        # 엑셀 파일 읽기
                        df = pd.read_excel(eye_file)
                        
                        # Time 행과 Area 행을 따로 생성
                        time_row = {
                            'participant': get_folder_number(participant_path),
                            'UT-HED': 1,
                            'Environment': env_num
                        }
                        area_row = {
                            'participant': get_folder_number(participant_path),
                            'UT-HED': 1,
                            'Environment': env_num
                        }
                        
                        # Sequence별 Time과 Area 정보 추가
                        max_sequence = df['Sequence'].max()
                        for seq in range(1, max_sequence + 1):
                            seq_data = df[df['Sequence'] == seq]
                            col_name = str(seq)
                            
                            if not seq_data.empty:
                                time_row[col_name] = seq_data['Time (s)'].iloc[0]
                                area_value = seq_data['Area'].iloc[0]
                                area_row[col_name] = f"{area_value} " if pd.notna(area_value) else ''
                            else:
                                time_row[col_name] = ''
                                area_row[col_name] = ''
                        
                        # 두 행을 DataFrame에 추가 (Area 행이 먼저, Time 행이 나중에)
                        final_df = pd.concat([final_df, pd.DataFrame([area_row, time_row])], ignore_index=True)
                        self.log_message(f"Environment {env_num} 처리 완료")
                        
                    except Exception as e:
                        self.log_message(f"Error processing file {eye_file}: {str(e)}")
            
            if not final_df.empty:
                # 컬럼 순서 재정렬
                base_cols = ['participant', 'UT-HED', 'Environment']
                seq_cols = [str(i) for i in range(1, final_df.shape[1])]
                seq_cols = [col for col in seq_cols if col in final_df.columns]
                
                final_df = final_df[base_cols + seq_cols]
                
                save_path = os.path.join(os.getcwd(), 'combined_eye_data.csv')
                final_df.to_csv(save_path, index=False)
                self.log_message(f"데이터 처리가 완료되었습니다.")
                self.log_message(f"결과가 다음 위치에 저장되었습니다: {save_path}")
                
                try:
                    open_file_explorer(save_path)
                except Exception as e:
                    self.log_message(f"파일 탐색기를 여는 중 오류 발생: {str(e)}")
            else:
                self.log_message("처리할 데이터가 없습니다.")
                
        except Exception as e:
            self.log_message(f"처리 중 오류 발생: {str(e)}")
        
        finally:
            self.root.after(0, self.processing_finished)
    
    def processing_finished(self):
        self.progress.stop()
        self.process_btn['state'] = 'normal'
        self.select_btn['state'] = 'normal'
        self.log_message("작업이 완료되었습니다.")

def open_file_explorer(path):
    """파일 탐색기에서 경로 열기"""
    if platform.system() == "Windows":
        os.startfile(os.path.dirname(path))
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", os.path.dirname(path)])
    else:  # linux
        subprocess.run(["xdg-open", os.path.dirname(path)])

def main():
    root = tk.Tk()
    app = EyeDataProcessor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
