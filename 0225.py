import csv

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

def process_eye_data(input_file, output_file, areas):
    """시선 데이터를 처리하여 영역별 시간을 계산하는 함수"""
    with open(input_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        
        # 결과 파일 준비
        with open(output_file, 'w', newline='') as out_f:
            writer = csv.writer(out_f)
            writer.writerow(["Area", "Time difference"])  # 헤더 작성
            
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
                
                # 결과에 추가
                writer.writerow([area, time_diff])

def merge_consecutive_areas(input_file, output_file):
    """연속된 같은 영역의 시간을 합산하는 함수"""
    with open(input_file, 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)  # 헤더 읽기
        
        # 결과 파일 준비
        with open(output_file, 'w', newline='') as out_f:
            writer = csv.writer(out_f)
            writer.writerow(header)  # 헤더 작성
            
            current_area = None
            accumulated_time = 0
            
            for row in reader:
                area = row[0]
                try:
                    time_diff = float(row[1])
                except ValueError:
                    time_diff = 0
                
                # 첫 번째 행이거나 영역이 변경된 경우
                if current_area is None:
                    current_area = area
                    accumulated_time = time_diff
                elif area != current_area:
                    # 이전 영역의 누적 시간 기록 (소수점 3자리까지 반올림)
                    writer.writerow([current_area, round(accumulated_time, 3)])
                    # 새 영역 시작
                    current_area = area
                    accumulated_time = time_diff
                else:
                    # 같은 영역이 계속되는 경우 시간 누적
                    accumulated_time += time_diff
            
            # 마지막 영역 기록 (소수점 3자리까지 반올림)
            if current_area is not None:
                writer.writerow([current_area, round(accumulated_time, 3)])

def process_and_merge_direct(input_file, output_file, areas):
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
    
    # 2단계: 연속된 같은 영역 합산하여 파일에 저장
    with open(output_file, 'w', newline='') as out_f:
        writer = csv.writer(out_f)
        writer.writerow(["Area", "Time difference"])  # 헤더 작성
        
        if not area_time_pairs:
            return  # 데이터가 없으면 종료
        
        current_area = area_time_pairs[0][0]
        accumulated_time = area_time_pairs[0][1]
        
        for i in range(1, len(area_time_pairs)):
            area, time_diff = area_time_pairs[i]
            
            if area != current_area:
                # 이전 영역의 누적 시간 기록 (소수점 3자리까지 반올림)
                writer.writerow([current_area, round(accumulated_time, 3)])
                # 새 영역 시작
                current_area = area
                accumulated_time = time_diff
            else:
                # 같은 영역이 계속되는 경우 시간 누적
                accumulated_time += time_diff
        
        # 마지막 영역 기록 (소수점 3자리까지 반올림)
        writer.writerow([current_area, round(accumulated_time, 3)])

# 메인 실행 코드
if __name__ == "__main__":
    # 영역 정의
    areas = {
        "Product":{
            "A": {"Xstart": -0.042, "Xend": 1.067, "Zstart": -9.123, "Zend": -5.772},
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
    
    # 데이터 처리 및 합산 실행 (임시 파일 없이)
    merged_file = "EyeData1_merged.csv"
    process_and_merge_direct("EyeData1.csv", merged_file, areas)
    print(f"처리 완료: {merged_file} 파일이 생성되었습니다.")