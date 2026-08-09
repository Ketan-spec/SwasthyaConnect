from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.services.ai_service import AIService

class AIAssistantWorker(QThread):
    chunk_received = pyqtSignal(str)
    finished_stream = pyqtSignal()
    
    def __init__(self, system_prompt, question, model_name):
        super().__init__()
        self.system_prompt = system_prompt
        self.question = question
        self.model_name = model_name
        
    def run(self):
        try:
            for chunk in AIService.chat_with_assistant_stream(self.system_prompt, self.question, self.model_name):
                self.chunk_received.emit(chunk)
        except Exception as e:
            self.chunk_received.emit(str(e))
        self.finished_stream.emit()

class ChatbotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("🤖 AI Health Assistant")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f766e;")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        # Removed model combo
        
        # Chat History
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.chat_history)
        
        # Input Area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your health question here...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 14px;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("Ask")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d9488;
                color: white;
                border-radius: 20px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0f766e;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        # Initial Greeting
        self.append_message("Assistant", "Hello! I am your Swasthya AI Assistant. How can I help you today? (Ask me general health and wellness questions.)")

    def send_message(self):
        user_text = self.input_field.text().strip()
        if not user_text:
            return
            
        self.append_message("You", user_text)
        self.input_field.clear()
        
        self.send_btn.setEnabled(False)
        self.chat_history.append("<i>Thinking...</i>")
        self.first_chunk = True
        self.current_response_text = ""
        
        model_name = "qwen2.5:3b"
        system_prompt = "You are a friendly health and wellness assistant. Provide general, safe advice. Never prescribe drugs natively. Warn the user to see a doctor for serious issues."
        
        self.worker = AIAssistantWorker(system_prompt, user_text, model_name)
        self.worker.chunk_received.connect(self.on_chunk)
        self.worker.finished_stream.connect(self.on_finished)
        self.worker.start()
        
    def on_chunk(self, chunk):
        if self.first_chunk:
            html = self.chat_history.toHtml()
            html = html.replace("<i>Thinking...</i>", "")
            self.chat_history.setHtml(html)
            self.chat_history.append('<div style="color:#0d9488; margin-bottom: 0px;"><b>Assistant:</b> </div>')
            self.first_chunk = False
            
        self.current_response_text += chunk
        self.chat_history.moveCursor(self.chat_history.textCursor().MoveOperation.End)
        self.chat_history.insertPlainText(chunk)
        
        # Auto-scroll to bottom
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_finished(self):
        self.chat_history.append("<br>")
        self.send_btn.setEnabled(True)
        
    def append_message(self, sender, text):
        color = "#0d9488" if sender == "Assistant" else "#1f2937"
        formatted_text = f'<div style="color:{color}; margin-bottom: 5px;"><b>{sender}:</b> {text}</div><br>'
        self.chat_history.append(formatted_text)
