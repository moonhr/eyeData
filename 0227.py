import pandas as pd
import numpy as np

def process_eye_data(file_path):
    # CSV 파일 읽기
    df = pd.read_csv(file_path)
    print(f"CSV 파일 '{file_path}' 읽기 완료")
    
    # 데이터 구조 파악
    # 홀수 행은 영역(알파벳), 짝수 행은 관찰 시간(초)
    
    # 각 참가자별로 처리
    unique_participants = df['participant'].unique()
    print(f"총 {len(unique_participants)}명의 참가자 데이터 처리 시작")
    
    for participant in unique_participants:
        print(f"참가자 {participant} 데이터 처리 중...")
        # 참가자 데이터 추출
        participant_data = df[df['participant'] == participant].copy()
        
        # 영역 데이터와 시간 데이터 분리
        area_rows = participant_data.iloc[::2].reset_index(drop=True)  # 홀수 행 (영역)
        time_rows = participant_data.iloc[1::2].reset_index(drop=True)  # 짝수 행 (시간)
        print(f"  참가자 {participant}의 영역 행 {len(area_rows)}개, 시간 행 {len(time_rows)}개 분리 완료")
        
        # 숫자 열만 선택 (1부터 시작하는 열)
        numeric_cols = [str(i) for i in range(1, len(area_rows.columns) - 3)]
        print(f"  처리할 열 수: {len(numeric_cols)}개")
        
        # 데이터를 numpy 배열로 변환하여 처리 속도 향상
        area_array = area_rows[numeric_cols].values
        time_array = time_rows[numeric_cols].astype(float).values
        
        print(f"  0.1초 이하 값 처리 중...")
        
        # 처리된 셀 수를 추적하기 위한 카운터
        processed_cells = 0
        
        # 각 행에 대해 처리
        for row_idx in range(len(area_array)):
            if row_idx % 10 == 0:  # 10행마다 진행상황 출력
                print(f"    행 {row_idx+1}/{len(area_array)} 처리 중 ({(row_idx+1)/len(area_array)*100:.1f}%)")
            
            # 각 열을 순회하면서 0.1초 이하 값 처리
            col_idx = 1  # 첫 번째 열은 건너뜀
            while col_idx < len(numeric_cols) - 1:  # 마지막 열 전까지
                # 현재 셀의 시간이 0.1초 이하인지 확인
                current_time = time_array[row_idx, col_idx]
                
                if 0 < current_time <= 0.1:
                    # 앞뒤 프레임의 시간 비교
                    prev_time = time_array[row_idx, col_idx - 1]
                    next_time = time_array[row_idx, col_idx + 1]
                    
                    # 디버깅 정보 출력
                    if row_idx < 3 and processed_cells < 10:  # 처음 몇 개의 처리만 출력
                        print(f"      처리: 행={row_idx+1}, 열={col_idx+1}, 값={current_time}, 이전={prev_time}, 다음={next_time}")
                    
                    # 앞뒤 프레임 중 더 긴 시간을 가진 영역으로 대체하고 시간 더하기
                    if prev_time >= next_time and prev_time > 0:
                        # 이전 셀에 현재 시간 더하기
                        area_array[row_idx, col_idx] = area_array[row_idx, col_idx - 1]
                        time_array[row_idx, col_idx - 1] += current_time
                        time_array[row_idx, col_idx] = 0
                        processed_cells += 1
                    elif next_time > 0:
                        # 다음 셀에 현재 시간 더하기
                        area_array[row_idx, col_idx] = area_array[row_idx, col_idx + 1]
                        time_array[row_idx, col_idx + 1] += current_time
                        time_array[row_idx, col_idx] = 0
                        processed_cells += 1
                    else:
                        # 앞뒤 모두 0이면 그냥 다음으로 넘어감
                        col_idx += 1
                        continue
                    
                    # 연속된 0.1초 이하 값을 처리하기 위해 인덱스를 증가시키지 않고 다시 검사
                    continue
                
                # 0.1초 이하가 아니면 다음 열로 이동
                col_idx += 1
        
        print(f"  총 {processed_cells}개의 0.1초 이하 셀 처리 완료")
        
        # 배열을 다시 데이터프레임으로 변환
        print("  처리된 배열을 데이터프레임으로 변환 중...")
        for col_idx, col in enumerate(numeric_cols):
            area_rows[col] = area_array[:, col_idx]
            time_rows[col] = time_array[:, col_idx]
        
        # 이어지는 동일 영역 통합
        print("  이어지는 동일 영역 통합 중...")
        for row_idx in range(len(area_rows)):
            if row_idx % 10 == 0:  # 10행마다 진행상황 출력
                print(f"    행 {row_idx+1}/{len(area_rows)} 처리 중 ({(row_idx+1)/len(area_rows)*100:.1f}%)")
            
            for col_idx in range(1, len(numeric_cols)):
                curr_col = numeric_cols[col_idx]
                prev_col = numeric_cols[col_idx - 1]
                
                # 현재 영역과 이전 영역이 같으면 시간 통합
                if area_rows.loc[row_idx, curr_col] == area_rows.loc[row_idx, prev_col]:
                    # 시간 합치기
                    time_rows.loc[row_idx, curr_col] = pd.to_numeric(time_rows.loc[row_idx, prev_col], errors='coerce') + pd.to_numeric(time_rows.loc[row_idx, curr_col], errors='coerce')
                    # 이전 영역과 시간 비우기
                    area_rows.loc[row_idx, prev_col] = ''
                    time_rows.loc[row_idx, prev_col] = 0
        
        # 처리된 값(0)과 빈 영역 삭제
        print("  처리된 값(0)과 빈 영역 삭제 중...")
        for row_idx in range(len(area_rows)):
            if row_idx % 10 == 0:  # 10행마다 진행상황 출력
                print(f"    행 {row_idx+1}/{len(area_rows)} 처리 중 ({(row_idx+1)/len(area_rows)*100:.1f}%)")
            
            for col_idx in range(len(numeric_cols)):
                col = numeric_cols[col_idx]
                
                # 시간이 0이거나 영역이 비어있으면 둘 다 삭제
                if time_rows.loc[row_idx, col] == 0 or pd.isna(time_rows.loc[row_idx, col]) or area_rows.loc[row_idx, col] == '':
                    area_rows.loc[row_idx, col] = np.nan
                    time_rows.loc[row_idx, col] = np.nan
        
        # 시간 값을 소수점 세 자리까지만 표시하도록 반올림
        for i in range(len(time_rows)):
            for col in time_rows.columns:
                if col not in ['participant', 'UT-HED', 'Environment'] and pd.notna(time_rows.iloc[i][col]):
                    # 문자열인 경우 숫자로 변환 후 반올림
                    try:
                        time_rows.at[i, col] = round(float(time_rows.iloc[i][col]), 3)
                    except (ValueError, TypeError):
                        # 숫자로 변환할 수 없는 경우 원래 값 유지
                        pass
        
        # 처리된 데이터를 원래 데이터프레임에 다시 삽입
        print("  처리된 데이터 삽입 중...")
        participant_indices = df.index[df['participant'] == participant].tolist()
        
        for i in range(len(area_rows)):
            if i % 10 == 0:  # 10행마다 진행상황 출력
                print(f"    행 {i+1}/{len(area_rows)} 삽입 중 ({(i+1)/len(area_rows)*100:.1f}%)")
            
            # 인덱스를 직접 사용하여 데이터프레임 업데이트
            area_idx = participant_indices[i*2]
            time_idx = participant_indices[i*2+1]
            
            # 모든 열에 대해 업데이트
            for col in df.columns:
                if col in area_rows.columns:
                    df.at[area_idx, col] = area_rows.iloc[i][col]
                    if col not in ['participant', 'UT-HED', 'Environment']:
                        try:
                            if pd.notna(time_rows.iloc[i][col]):
                                df.at[time_idx, col] = round(float(time_rows.iloc[i][col]), 3)
                            else:
                                df.at[time_idx, col] = time_rows.iloc[i][col]
                        except (ValueError, TypeError):
                            df.at[time_idx, col] = time_rows.iloc[i][col]
                    else:
                        df.at[time_idx, col] = time_rows.iloc[i][col]
        
        print(f"참가자 {participant} 데이터 처리 완료")
    
    # 처리된 데이터 저장
    output_file = file_path.replace('.csv', '_processed.csv')
    print(f"처리된 데이터를 {output_file}에 저장 중...")
    df.to_csv(output_file, index=False)
    print("저장 완료!")
    
    return output_file

# 파일 경로를 지정하여 함수 실행
print("데이터 처리 시작")
# 여기에 파일명 입력. 파일은 코드와 같은 위치에 둘 것.
processed_file = process_eye_data('data_House2.csv')
print(f"처리된 파일이 저장되었습니다: {processed_file}")
print("모든 작업 완료!")
