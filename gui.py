import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                           QWidget, QFileDialog, QTextEdit, QLabel)
from PyQt5.QtCore import QThread, pyqtSignal
import save

class DataProcessThread(QThread):
    progress_signal = pyqtSignal(str)
    
    def run(self):
        try:
            self.progress_signal.emit("데이터 처리를 시작합니다...")
            save.process_eye_data()
            self.progress_signal.emit("처리가 완료되었습니다!")
        except Exception as e:
            self.progress_signal.emit(f"에러 발생: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Eye Data Processor')
        self.setGeometry(100, 100, 600, 400)
        
        # 메인 위젯과 레이아웃 설정
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        
        # 상태 표시 레이블
        self.status_label = QLabel('House 폴더를 선택해주세요')
        layout.addWidget(self.status_label)
        
        # 폴더 선택 버튼
        self.select_btn = QPushButton('폴더 선택')
        self.select_btn.clicked.connect(self.select_folder)
        layout.addWidget(self.select_btn)
        
        # 처리 시작 버튼
        self.process_btn = QPushButton('처리 시작')
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)
        
        # 로그 표시 영역
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        main_widget.setLayout(layout)
        
    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, '폴더 선택')
        if folder_path:
            # 선택된 폴더의 이름이 'House'인지 확인
            folder_name = os.path.basename(folder_path)
            if folder_name == 'House':
                # 작업 디렉토리를 House 폴더의 부모 디렉토리로 변경
                os.chdir(os.path.dirname(folder_path))
                self.status_label.setText(f'선택된 폴더: {folder_path}')
                self.process_btn.setEnabled(True)
                self.log_text.append(f'House 폴더가 선택되었습니다: {folder_path}')
            else:
                self.status_label.setText('올바른 폴더가 아닙니다. House 폴더를 선택해주세요.')
                self.process_btn.setEnabled(False)
    
    def start_processing(self):
        self.process_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.log_text.append("데이터 처리를 시작합니다...")
        
        # 처리 스레드 시작
        self.thread = DataProcessThread()
        self.thread.progress_signal.connect(self.update_log)
        self.thread.finished.connect(self.processing_finished)
        self.thread.start()
    
    def update_log(self, message):
        self.log_text.append(message)
    
    def processing_finished(self):
        self.process_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        self.log_text.append("작업이 완료되었습니다.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 