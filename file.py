import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import zipfile
from datetime import datetime

def process_eye_tracking_data(input_file):
    try:
        # CSV 파일에서 아이트래킹 데이터 로드
        df = pd.read_csv(input_file)

        # 각 제품 영역의 좌표 정보 정의
        areas = {
            "A": {"Xstart": -0.042, "Xend": 1.067, "Zstart": -9.123, "Zend": -5.772},
            "B": {"Xstart": -6.015, "Xend": -1.964, "Zstart": -9.531, "Zend": -8.467},
            "C": {"Xstart": -6.015, "Xend": -1.964, "Zstart": -6.522, "Zend": -5.472},
            "D": {"Xstart": -9.031, "Xend": -5.996, "Zstart": -11.925, "Zend": -11.314},
            "E": {"Xstart": -5.019, "Xend": -1.999, "Zstart": -11.925, "Zend": -11.314},
            "F": {"Xstart": -1.032, "Xend": 2.05, "Zstart": -11.925, "Zend": -11.314},
            "G": {"Xstart": -9.031, "Xend": -5.996, "Zstart": -4, "Zend": -3.01},
            "H": {"Xstart": -5.019, "Xend": -1.999, "Zstart": -4, "Zend": -3.01},
            "I": {"Xstart": -1.032, "Xend": 2.05, "Zstart": -4, "Zend": -3.01}
        }

        # 제품 영역을 저장할 새로운 열 생성
        df["ProductArea"] = ""

        # 좌표값을 기준으로 각 데이터 포인트가 어느 영역에 속하는지 확인
        for index, row in df.iterrows():
            x = row["Gaze PositionX"]
            z = row["Gaze PositionZ"]
            
            for area_name, area_coords in areas.items():
                if area_coords["Xstart"] <= x <= area_coords["Xend"] and area_coords["Zstart"] <= z <= area_coords["Zend"]:
                    df.loc[index, "ProductArea"] = area_name
                    break

        # 짧은 시간 동안의 영역 이탈을 보정
        for i in range(1, len(df) - 1):
            if df.loc[i, "ProductArea"] == "" or df.loc[i, "ProductArea"] != df.loc[i - 1, "ProductArea"]:
                if df.loc[i - 1, "ProductArea"] == df.loc[i + 1, "ProductArea"]:
                    df.loc[i, "ProductArea"] = df.loc[i - 1, "ProductArea"]

        # 0.1초 미만의 영역 변화 처리
        current_area = None
        start_time = 0
        min_duration = 0.1

        for i in range(len(df)):
            if df.loc[i, "ProductArea"] != current_area:
                if current_area is not None:
                    duration = df.loc[i-1, "Time (s)"] - start_time
                    if duration < min_duration:
                        df.loc[start_index:i-1, "ProductArea"] = ""
                
                current_area = df.loc[i, "ProductArea"]
                start_time = df.loc[i, "Time (s)"]
                start_index = i

        # 시간 순서대로 영역별 체류 시간 계산
        current_area = None
        start_time = 0
        area_sequence = []

        for i in range(len(df)):
            if df.loc[i, "ProductArea"] != current_area:
                if current_area is not None:
                    duration = round(df.loc[i-1, "Time (s)"] - start_time, 3)
                    area_sequence.append((current_area, duration))
                
                current_area = df.loc[i, "ProductArea"]
                start_time = df.loc[i, "Time (s)"]

        # 마지막 영역 처리
        if current_area is not None:
            duration = round(df.loc[len(df)-1, "Time (s)"] - start_time, 3)
            area_sequence.append((current_area, duration))

        # 새로운 데이터프레임 생성
        sequence_df = pd.DataFrame(columns=['Sequence', 'Area', 'Time (s)'])

        # 데이터 추가
        for idx, (area, duration) in enumerate(area_sequence, 1):
            new_row = {'Sequence': idx, 'Area': area, 'Time (s)': duration}
            sequence_df = pd.concat([sequence_df, pd.DataFrame([new_row])], ignore_index=True)

        # 시간 열의 표시 형식을 소수점 3자리로 설정
        sequence_df['Time (s)'] = sequence_df['Time (s)'].round(3)

        # 결과 파일 저장
        output_dir = os.path.dirname(input_file)
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        
        sequence_output = os.path.join(output_dir, f"{base_name}_sequence_result.xlsx")
        processed_output = os.path.join(output_dir, f"{base_name}_with_Area.xlsx")
        
        sequence_df.to_excel(sequence_output, index=False)
        df.to_excel(processed_output, index=False)
        
        return True, "처리가 완료되었습니다."
        
    except Exception as e:
        return False, f"오류가 발생했습니다: {str(e)}"

def count_total_files(root_dir):
    """전체 처리할 파일 수를 계산"""
    total = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if "Eye" in dirpath:
            total += len([f for f in filenames if f.startswith('EyeData') and f.endswith('.csv')])
    return total

def update_progress(progress_var, progress_label, current, total, current_file):
    """프로그레스 바와 레이블 업데이트"""
    progress = (current / total) * 100
    progress_var.set(progress)
    progress_label.config(text=f"처리 중... ({current}/{total})\n현재 파일: {current_file}")
    root.update()

def process_directory(root_dir, progress_var, progress_label):
    try:
        # 전체 파일 수 계산
        total_files = count_total_files(root_dir)
        if total_files == 0:
            return False, "처리할 EyeData CSV 파일을 찾을 수 없습니다."
            
        # 결과를 저장할 임시 디렉토리 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = os.path.join(root_dir, f"results_{timestamp}")
        os.makedirs(temp_dir, exist_ok=True)
        
        processed_count = 0
        
        # 모든 하위 디렉토리 탐색
        for dirpath, dirnames, filenames in os.walk(root_dir):
            if "Eye" in dirpath:
                csv_files = [f for f in filenames if f.startswith('EyeData') and f.endswith('.csv')]
                
                for csv_file in csv_files:
                    try:
                        # 진행 상황 업데이트
                        processed_count += 1
                        update_progress(progress_var, progress_label, processed_count, total_files, csv_file)
                        
                        input_path = os.path.join(dirpath, csv_file)
                        
                        # 원본 경로 구조 유지
                        rel_path = os.path.relpath(dirpath, root_dir)
                        output_dir = os.path.join(temp_dir, rel_path)
                        os.makedirs(output_dir, exist_ok=True)
                        
                        base_name = os.path.splitext(csv_file)[0]
                        sequence_output = os.path.join(output_dir, f"{base_name}_sequence_result.xlsx")
                        processed_output = os.path.join(output_dir, f"{base_name}_with_Area.xlsx")
                        
                        # 데이터 처리
                        process_eye_tracking_data(input_path)
                        
                    except Exception as e:
                        print(f"파일 처리 중 오류 발생 ({csv_file}): {str(e)}")
                        continue
        
        # 압축 진행 상황 표시
        progress_label.config(text="결과 파일 압축 중...")
        root.update()
        
        # 결과 파일들을 ZIP 파일로 압축
        zip_path = os.path.join(root_dir, f"eye_tracking_results_{timestamp}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for dirpath, dirnames, filenames in os.walk(temp_dir):
                for file in filenames:
                    file_path = os.path.join(dirpath, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        # 임시 디렉토리 삭제
        import shutil
        shutil.rmtree(temp_dir)
        
        # 완료 표시
        progress_var.set(100)
        progress_label.config(text="처리 완료!")
        
        return True, f"총 {total_files}개 파일 처리 완료\n결과가 {os.path.basename(zip_path)}에 저장되었습니다."
        
    except Exception as e:
        return False, f"처리 중 오류가 발생했습니다: {str(e)}"

def select_directory():
    global selected_path
    selected_path = filedialog.askdirectory(title="House 폴더 선택")
    
    if selected_path:
        file_label.config(text=f"선택된 폴더: {os.path.basename(selected_path)}")

def process_files():
    if not selected_path:
        messagebox.showwarning("경고", "먼저 House 폴더를 선택해주세요.")
        return
    
    # 버튼 비활성화
    select_button.config(state='disabled')
    process_button.config(state='disabled')
    
    try:
        success, message = process_directory(selected_path, progress_var, progress_label)
        if success:
            messagebox.showinfo("완료", message)
        else:
            messagebox.showerror("오류", message)
    except Exception as e:
        messagebox.showerror("오류", f"처리 중 오류가 발생했습니다: {str(e)}")
    finally:
        # 버튼 다시 활성화
        select_button.config(state='normal')
        process_button.config(state='normal')
        # 프로그레스 바와 레이블 초기화
        progress_var.set(0)
        progress_label.config(text="")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        root.title("아이트래킹 데이터 분석기")
        root.geometry("500x400")
        root.deiconify()

        frame = tk.Frame(root)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        # 설명 레이블
        label = tk.Label(frame, text="House 폴더를 선택하세요", pady=20)
        label.pack()

        # 폴더 선택 버튼
        global select_button
        select_button = tk.Button(frame, text="폴더 선택", command=select_directory, padx=20, pady=10)
        select_button.pack()

        # 선택된 폴더 표시 레이블
        global file_label, selected_path
        selected_path = ""
        file_label = tk.Label(frame, text="선택된 폴더: 없음", pady=10)
        file_label.pack()

        # 프로그레스 바
        global progress_var
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(frame, length=300, mode='determinate', variable=progress_var)
        progress_bar.pack(pady=10)

        # 진행 상황 레이블
        global progress_label
        progress_label = tk.Label(frame, text="", pady=10)
        progress_label.pack()

        # 실행 버튼
        global process_button
        process_button = tk.Button(frame, text="실행", command=process_files, padx=20, pady=10)
        process_button.pack(pady=20)

        root.mainloop()
    except Exception as e:
        print(f"오류 발생: {str(e)}")