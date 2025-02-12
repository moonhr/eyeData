# 아이트래킹 데이터에서 제품 영역을 식별하고 처리하는 스크립트

# pandas 라이브러리 임포트
import pandas as pd

# CSV 파일에서 아이트래킹 데이터 로드
df = pd.read_csv(r"C:/Users/fksrl/OneDrive/바탕 화면/2024 Experimental Folder/2024 Experimental Folder/참가자 폴더/House/1/Eye/EyeData1.csv")

# 각 제품 영역의 좌표 정보 정의
# 각 영역은 X축과 Z축의 시작과 끝 좌표로 정의됨
areas = {
    "A": {"Xstart": -0.042, "Xend": 1.067, "Zstart": -9.123, "Zend": -5.772},  # A 영역 좌표
    "B": {"Xstart": -6.015, "Xend": -1.964, "Zstart": -9.531, "Zend": -8.467}, # B 영역 좌표
    "C": {"Xstart": -6.015, "Xend": -1.964, "Zstart": -6.522, "Zend": -5.472}, # C 영역 좌표
    "D": {"Xstart": -9.031, "Xend": -5.996, "Zstart": -11.925, "Zend": -11.314}, # D 영역 좌표
    "E": {"Xstart": -5.019, "Xend": -1.999, "Zstart": -11.925, "Zend": -11.314}, # E 영역 좌표
    "F": {"Xstart": -1.032, "Xend": 2.05, "Zstart": -11.925, "Zend": -11.314},   # F 영역 좌표
    "G": {"Xstart": -9.031, "Xend": -5.996, "Zstart": -4, "Zend": -3.01},     # G 영역 좌표
    "H": {"Xstart": -5.019, "Xend": -1.999, "Zstart": -4, "Zend": -3.01},     # H 영역 좌표
    "I": {"Xstart": -1.032, "Xend": 2.05, "Zstart": -4, "Zend": -3.01}        # I 영역 좌표
}

# 제품 영역을 저장할 새로운 열 생성
df["ProductArea"] = ""

# 좌표값을 기준으로 각 데이터 포인트가 어느 영역에 속하는지 확인
for index, row in df.iterrows():
    x = row["Gaze PositionX"]  # X 좌표
    z = row["Gaze PositionZ"]  # Z 좌표
    t = row["Time (s)"]        # 시간 정보
    
    # 각 영역을 순회하면서 현재 좌표가 어느 영역에 속하는지 확인
    for area_name, area_coords in areas.items():
        if area_coords["Xstart"] <= x <= area_coords["Xend"] and area_coords["Zstart"] <= z <= area_coords["Zend"]:
            df.loc[index, "ProductArea"] = area_name
            break

# 짧은 시간 동안의 영역 이탈을 보정
# 앞뒤 데이터가 같은 영역일 경우, 중간 데이터도 같은 영역으로 처리
for i in range(1, len(df) - 1):
    if df.loc[i, "ProductArea"] == "" or df.loc[i, "ProductArea"] != df.loc[i - 1, "ProductArea"]:
        if df.loc[i - 1, "ProductArea"] == df.loc[i + 1, "ProductArea"]:
            df.loc[i, "ProductArea"] = df.loc[i - 1, "ProductArea"]

# 0.1초 미만의 영역 변화 처리
# 연속된 같은 영역을 그룹화하고 지속 시간이 0.1초 미만인 영역은 제거
current_area = None
start_time = 0
min_duration = 0.1  # 최소 지속 시간 설정 (0.1초)

for i in range(len(df)):
    if df.loc[i, "ProductArea"] != current_area:
        if current_area is not None:
            duration = df.loc[i-1, "Time (s)"] - start_time
            # 이전 영역의 지속 시간이 0.1초 미만이면 해당 영역 제거
            if duration < min_duration:
                df.loc[start_index:i-1, "ProductArea"] = ""
        
        current_area = df.loc[i, "ProductArea"]
        start_time = df.loc[i, "Time (s)"]
        start_index = i

# 마지막 영역 처리
if current_area is not None:
    duration = df.loc[len(df)-1, "Time (s)"] - start_time
    if duration < min_duration:
        df.loc[start_index:, "ProductArea"] = ""

# 시간 순서대로 영역별 체류 시간 계산
current_area = None
start_time = 0
area_sequence = []

for i in range(len(df)):
    if df.loc[i, "ProductArea"] != current_area:
        if current_area is not None:
            duration = round(df.loc[i-1, "Time (s)"] - start_time, 3)  # 소수점 3자리로 반올림
            area_sequence.append((current_area, duration))
        
        current_area = df.loc[i, "ProductArea"]
        start_time = df.loc[i, "Time (s)"]

# 마지막 영역 처리
if current_area is not None:
    duration = round(df.loc[len(df)-1, "Time (s)"] - start_time, 3)  # 소수점 3자리로 반올림
    area_sequence.append((current_area, duration))

# 새로운 데이터프레임 생성
sequence_df = pd.DataFrame(columns=['Sequence', 'Area', 'Time (s)'])

# 데이터 추가
for idx, (area, duration) in enumerate(area_sequence, 1):
    new_row = {'Sequence': idx, 'Area': area, 'Time (s)': duration}
    sequence_df = pd.concat([sequence_df, pd.DataFrame([new_row])], ignore_index=True)

# 시간 열의 표시 형식을 소수점 3자리로 설정
sequence_df['Time (s)'] = sequence_df['Time (s)'].round(3)

# 새로운 엑셀 파일로 저장
sequence_df.to_excel(r"C:/Users/fksrl/OneDrive/바탕 화면/2024 Experimental Folder/2024 Experimental Folder/참가자 폴더/House/1/Eye/sequence_result.xlsx", index=False)

# 엑셀 파일 저장 전에 결과 문자열을 데이터프레임에 추가
# df["AreaSequence"] = result_string

# 처리된 데이터를 엑셀 파일로 저장
df.to_excel(r"C:/Users/fksrl/OneDrive/바탕 화면/2024 Experimental Folder/2024 Experimental Folder/참가자 폴더/House/1/Eye/EyeData1_with_Area.xlsx", index=False)
