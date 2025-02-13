import os
import pandas as pd
import glob

def process_eye_data():
    # 결과를 저장할 빈 DataFrame 생성
    final_df = pd.DataFrame()
    
    # House 폴더 내의 모든 참가자 폴더 검색
    participant_folders = glob.glob('House/*')
    
    for participant_path in participant_folders:
        participant_num = os.path.basename(participant_path)
        
        # 각 참가자 폴더 내의 Eye 폴더에서 모든 EyeData 파일 검색
        eye_files = glob.glob(f'{participant_path}/Eye/EyeData*_sequence_result.csv')
        
        for eye_file in eye_files:
            # 파일명에서 Environment 번호 추출
            env_num = os.path.basename(eye_file).split('EyeData')[1].split('_')[0]
            
            try:
                # CSV 파일 읽기
                df = pd.read_csv(eye_file)
                
                # Sequence와 Time 컬럼만 선택하여 전치(transpose)
                sequence_data = df[['Sequence', 'Time (s)']].set_index('Sequence')
                row_data = sequence_data.T.iloc[0]
                
                # 새로운 행 데이터 생성
                row_dict = {
                    'participant': participant_num,
                    'UT-HED': 1,
                    'Environment': env_num
                }
                # Time 데이터 추가
                row_dict.update(row_data.to_dict())
                
                # 결과 DataFrame에 추가
                final_df = pd.concat([final_df, pd.DataFrame([row_dict])], ignore_index=True)
                
            except Exception as e:
                print(f"Error processing file {eye_file}: {str(e)}")
    
    # 결과 저장
    if not final_df.empty:
        final_df.to_csv('combined_eye_data.csv', index=False)
        print("데이터 처리가 완료되었습니다. 결과가 'combined_eye_data.csv'에 저장되었습니다.")
    else:
        print("처리할 데이터가 없습니다.")

if __name__ == "__main__":
    process_eye_data()
