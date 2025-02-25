import csv
import os
import glob
import tkinter as tk
from tkinter import filedialog, messagebox

def identify_area(x, z, layer_name, areas):
    """주어진 좌표와 레이어에 따라 영역을 식별하는 함수"""
    # Layer Name이 Default이거나 좌표가 0인 경우 'Z' 반환
    if layer_name == "Default" or (x == 0 and z == 0):
        return "Z"
        
    # 해당 레이어의 영역들만 확인
    if layer_name in areas:
        relevant_areas = areas[layer_name]
        
        for area_name, coords in relevant_areas.items():
            if (coords["Xstart"] <= x <= coords["Xend"] and 
                coords["Zstart"] <= z <= coords["Zend"]):
                return area_name
                
    # 어떤 영역에도 속하지 않으면 'Z' 반환
    return "Z"

def process_and_merge_direct(input_file, areas):
    """원본 데이터를 처리하고 연속된 영역을 합산하는 함수 (임시 파일 없이)"""
    # 1단계: 원본 데이터에서 영역 식별하여 메모리에 저장
    area_time_pairs = []
    
    with open(input_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # 필요한 데이터 추출
            try:
                x = float(row["Gaze PositionX"]) if row["Gaze PositionX"] else 0
                z = float(row["Gaze PositionZ"]) if row["Gaze PositionZ"] else 0
                layer_name = row["Layer Name"]
                time_diff = float(row["Time difference"]) if row["Time difference"] and row["Time difference"] != "#VALUE!" else 0
                velocity = float(row["Velocity"]) if row["Velocity"] and row["Velocity"] != "#VALUE!" else 0
            except ValueError:
                # 변환 오류 시 기본값 설정
                x, z, time_diff, velocity = 0, 0, 0, 0
            
            # 속도가 100 초과인 경우 'Z'로 설정
            if velocity > 100:
                area = "Z"
            else:
                # 영역 식별
                area = identify_area(x, z, layer_name, areas)
            
            # 메모리에 저장
            area_time_pairs.append((area, time_diff))
    
    # 2단계: 연속된 같은 영역 합산
    merged_data = []
    current_area = None
    accumulated_time = 0
    
    for area, time_diff in area_time_pairs:
        if current_area is None:
            # 첫 번째 영역 설정
            current_area = area
            accumulated_time = time_diff
        elif area == current_area:
            # 같은 영역이면 시간 누적
            accumulated_time += time_diff
        else:
            # 다른 영역이면 현재까지 누적된 영역 기록 (소수점 3자리까지 반올림)
            merged_data.append((current_area, round(accumulated_time, 3)))
            # 새 영역 설정
            current_area = area
            accumulated_time = time_diff
    
    # 마지막 영역 기록 (소수점 3자리까지 반올림)
    if current_area is not None:
        merged_data.append((current_area, round(accumulated_time, 3)))
    
    return merged_data

def process_folder(folder_path, output_file):
    """폴더 내의 모든 EyeData 파일을 처리하여 하나의 결과 파일로 만드는 함수"""
    areas = {
        "Product":{
            "A":{"Xstart": -0.042, "Xend": 1.067, "Zstart": -9.123, "Zend": -5.772},
            "B": {"Xstart": -6.015, "Xend": -1.964, "Zstart": -9.531, "Zend": -7.2},
            "C": {"Xstart": -6.015, "Xend": -1.964, "Zstart": -6.522, "Zend": -5.472},
            "D": {"Xstart": -9.031, "Xend": -5.996, "Zstart": -11.925, "Zend": -11.02},
            "E": {"Xstart": -5.019, "Xend": -1.999, "Zstart": -11.925, "Zend": -11.02},
            "F": {"Xstart": -1.032, "Xend": 2.05, "Zstart": -11.925, "Zend": -11.02},
            "G": {"Xstart": -9.031, "Xend": -5.996, "Zstart": -4, "Zend": -3.01},
            "H": {"Xstart": -5.019, "Xend": -1.999, "Zstart": -4, "Zend": -3.01},
            "I": {"Xstart": -1.032, "Xend": 2.05, "Zstart": -4, "Zend": -3.01}
        },
        "Nature":{
            # 자연 Plant 영역 좌표 정의
            "J":{"Xstart": 2.12, "Xend": 3.985, "Zstart": -11.958, "Zend": -10.3},
            "K":{"Xstart": -1.972, "Xend": -1.011, "Zstart": -11.958, "Zend": -10.3},
            "L":{"Xstart": -5.973, "Xend": -5.011, "Zstart": -11.958, "Zend": -10.3},
            "M":{"Xstart": -11.188, "Xend": -9.03, "Zstart": -11.958, "Zend": -10.3},
            "N":{"Xstart": -11.188, "Xend": -9.03, "Zstart": -5.733, "Zend": -2.92},
            "O":{"Xstart": -5.973, "Xend": -5.011, "Zstart": -5.773, "Zend": -2.92},
            "P":{"Xstart": -1.972, "Xend": -1.011, "Zstart": -5.773, "Zend": -2.92},
            "Q":{"Xstart": 2.12, "Xend": 3.985, "Zstart": -5.773, "Zend": -2.92},
            "R":{"Xstart": -8.683, "Xend": -8.299, "Zstart": -8.702, "Zend": -8.307},
            
            # 자연 Picture 영역 좌표 정의
            "S":{"Xstart": -9.029, "Xend": -5.996, "Zstart": -11.925, "Zend": -11.02},
            "T":{"Xstart": -5.01, "Xend": -1.999, "Zstart": -11.925, "Zend": -11.02},
            "U":{"Xstart": -1.01, "Xend": 2.05, "Zstart": -11.925, "Zend": -11.02},
            "V":{"Xstart": -9.029, "Xend": -5.996, "Zstart": -4, "Zend": -3.01},
            "W":{"Xstart": -5.01, "Xend": -1.999, "Zstart": -4, "Zend": -3.01},
            "X":{"Xstart": -1.01, "Xend": 2.05, "Zstart": -4, "Zend": -3.01}
        }
    }
    
    all_data = []  # [[areas_row1, times_row1], [areas_row2, times_row2], ...]
    header = ["participant", "UT-HED", "Environment"]
    max_columns = 3  # 시작 컬럼 수 (participant, UT-HED, Environment)
    
    # 1depth 폴더 탐색 (1,2,3,4,5...)
    for participant_folder in sorted(glob.glob(os.path.join(folder_path, "*"))):
        if os.path.isdir(participant_folder):
            participant_id = os.path.basename(participant_folder)
            
            try:
                participant_num = int(participant_id)
            except ValueError:
                continue
                
            eye_folder = os.path.join(participant_folder, "Eye")
            if not os.path.exists(eye_folder):
                continue
                
            # EyeData 파일 처리
            for eye_file in sorted(glob.glob(os.path.join(eye_folder, "EyeData*.csv"))):
                environment_num = os.path.basename(eye_file).replace("EyeData", "").replace(".csv", "")
                
                # 파일 데이터 처리
                areas_row, times_row = process_eye_data(eye_file, areas)
                
                # 기본 정보 추가
                areas_row = [participant_num, 1, environment_num] + areas_row
                times_row = [participant_num, 1, environment_num] + times_row
                
                all_data.append([areas_row, times_row])
                max_columns = max(max_columns, len(areas_row))

    # 결과 파일 작성
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # 헤더 생성 (1,1,1,1... 형식)
        header_nums = []
        for i in range((max_columns - 3)):
            header_nums.append(str(i+1))
        writer.writerow(header + header_nums)
        
        # 데이터 쓰기 (각 파일마다 두 행씩)
        for areas_row, times_row in all_data:
            # 부족한 열은 빈 값으로 채우기
            while len(areas_row) < max_columns:
                areas_row.append('')
            while len(times_row) < max_columns:
                times_row.append('')
            
            writer.writerow(areas_row)
            writer.writerow(times_row)

def process_eye_data(file_path, areas):
    """개별 EyeData 파일을 처리하는 함수"""
    areas_list = []
    times_list = []
    current_area = None
    current_time = 0
    
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                # 1. 각 행에서 좌표값과 시간 추출
                x = float(row.get('Gaze PositionX', 0))
                z = float(row.get('Gaze PositionZ', 0))
                time = float(row.get('Time difference', 0)) if row.get('Time difference') and row.get('Time difference') != "#VALUE!" else 0
                layer = row.get('Layer Name', 'Default')
                velocity = float(row.get('Velocity', 0)) if row.get('Velocity') and row.get('Velocity') != "#VALUE!" else 0
                
                # 속도가 100 초과인 경우 'Z'로 설정
                if velocity > 100:
                    area = "Z"
                else:
                    # 2. 좌표값으로 area 식별
                    area = identify_area(x, z, layer, areas)
                
                # 3. 연속된 area의 time 합산
                if area == current_area:
                    current_time += time  # 같은 area면 시간 누적
                else:
                    if current_area is not None:
                        # 다른 area가 나오면 이전 area와 누적 시간 저장
                        areas_list.append(current_area)
                        times_list.append(str(round(current_time, 3)))
                    # 새로운 area 시작
                    current_area = area
                    current_time = time
                    
            except (ValueError, TypeError):
                continue
                
        # 마지막 데이터 처리
        if current_area is not None:
            areas_list.append(current_area)
            times_list.append(str(round(current_time, 3)))
    
    return areas_list, times_list

def main():
    root = tk.Tk()
    root.withdraw()  # GUI 창 숨기기
    
    # 폴더 선택 대화상자
    folder_path = filedialog.askdirectory(title="처리할 폴더를 선택하세요")
    
    if folder_path:
        try:
            output_file = os.path.join(os.path.dirname(folder_path), 
                                     f"combined_eye_data_{os.path.basename(folder_path)}.csv")
            process_folder(folder_path, output_file)
            messagebox.showinfo("완료", f"처리가 완료되었습니다.\n결과 파일: {output_file}")
        except Exception as e:
            messagebox.showerror("오류", f"처리 중 오류가 발생했습니다: {str(e)}")
    else:
        messagebox.showwarning("경고", "폴더를 선택하지 않았습니다.")

if __name__ == "__main__":
    main()