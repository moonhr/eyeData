import pandas as pd
import os

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
            
            # 모든 좌표에 대해 area 확인
            for area_name, area_coords in areas.items():
                if area_coords["Xstart"] <= x <= area_coords["Xend"] and area_coords["Zstart"] <= z <= area_coords["Zend"]:
                    df.loc[index, "ProductArea"] = area_name
                    break
                else:
                    df.loc[index, "ProductArea"] = ""  # area가 없는 경우 빈 문자열 할당

        # 결과 파일 저장
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"{base_name}-area.csv"
        df.to_csv(output_file, index=False)
        
        print(f"처리가 완료되었습니다. 결과 파일: {output_file}")
        
    except Exception as e:
        print(f"오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    # 테스트할 파일 경로 지정
    input_file = "EyeData1.csv"  # 현재 디렉토리에 있는 파일 기준
    process_eye_tracking_data(input_file) 