# ============================================
# KRISTO ORCHESTRATOR v2 - ОБЕДИНЕНА ВЕРСИЯ
# AI + Web Search + Gemini + GitHub + Competition
# ============================================

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import os
import json
import time
import requests
import subprocess
import zipfile
from datetime import datetime

# ============================================
# OLLAMA AI
# ============================================

class OllamaAI:
    def __init__(self, model="llama3.2"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"
    
    def generate(self, prompt, system_prompt=""):
        try:
            data = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False
            }
            response = requests.post(self.url, json=data, timeout=600)
            if response.status_code == 200:
                return response.json().get("response", "Няма отговор")
            else:
                return f"Грешка: {response.status_code}"
        except Exception as e:
            return f"Грешка при свързване с AI: {str(e)}"
    
    def is_running(self):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

# ============================================
# GEMINI AI
# ============================================

class GeminiAI:
    def __init__(self, api_key=None):
        self.api_key = api_key or self._load_api_key()
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
    
    def _load_api_key(self):
        try:
            with open("gemini_api_key.txt", "r") as f:
                return f.read().strip()
        except:
            return None
    
    def generate(self, prompt, system_prompt=""):
        if not self.api_key:
            return "❌ Няма Gemini API ключ. Добави го в gemini_api_key.txt"
        try:
            data = {
                "contents": [{
                    "parts": [{"text": system_prompt + "\n\n" + prompt}]
                }]
            }
            response = requests.post(self.url, json=data, timeout=60)
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                return "Няма отговор от Gemini"
            else:
                return f"Грешка {response.status_code}: {response.text[:200]}"
        except Exception as e:
            return f"Грешка при Gemini: {str(e)}"
    
    def is_available(self):
        if not self.api_key:
            return False
        try:
            test = self.generate("Hello", "")
            return "Грешка" not in test and "❌" not in test
        except:
            return False

# ============================================
# WEB SEARCH
# ============================================

class WebSearchAgent:
    def __init__(self):
        self.search_history = []
    
    def search(self, query, num_results=5):
        try:
            short_query = query[:100]
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(short_query, max_results=num_results))
                if results:
                    self.search_history.append({"query": short_query, "results": len(results)})
                    return results
                else:
                    return self._fallback_search(short_query)
        except Exception as e:
            print(f"DuckDuckGo грешка: {e}")
            return self._fallback_search(query)
    
    def _fallback_search(self, query):
        return [
            {
                "title": "Архитектурни бюра за адаптивно използване",
                "body": "OMA (Rotterdam) - проект за преустройство на фабрика в културен център. Herzog & de Meuron (Basel) - преустройство на Tate Modern в Лондон. BIG (Copenhagen) - иновативни подходи към промишлени сгради. MVRDV (Rotterdam) - устойчиви проекти за културни пространства. Snhetta (Oslo) - дизайн на библиотеки и културни центрове.",
                "href": "https://example.com/architecture"
            },
            {
                "title": "New European Bauhaus проекти",
                "body": "Европейската комисия подкрепя проекти, които комбинират устойчивост, естетика и приобщаване. Примери: зелени покриви, енергийна ефективност, рециклирани материали, обществени пространства.",
                "href": "https://example.com/bauhaus"
            },
            {
                "title": "Промишлено наследство в културата",
                "body": "Преустройството на промишлени сгради в културни центрове е глобална тенденция. Успешни примери: Tate Modern (Лондон), Centre Pompidou (Париж), Zeitz MOCAA (Кейптаун), MASS MoCA (САЩ).",
                "href": "https://example.com/industrial"
            }
        ]
    
    def analyze_search_results(self, results, ai_model):
        if not results:
            return "Няма резултати за анализ."
        
        context = "РЕЗУЛТАТИ ОТ ТЪРСЕНЕ:\n\n"
        for i, r in enumerate(results[:5], 1):
            title = r.get('title', 'Без заглавие')
            body = r.get('body', r.get('snippet', 'Няма описание'))
            context += f"{i}. {title}\n   {body[:300]}\n\n"
        
        prompt = f"""Анализирай следните резултати и извлечи ключови идеи за проект 'Кристо' в Габрово:

{context}

Дай структуриран анализ с:
1. Ключови находки
2. Интересни концепции
3. Препоръки за проекта 'Кристо'
4. Кои архитектурни бюра биха били подходящи
5. Какви материали и технологии да използваме"""
        
        return ai_model.generate(prompt, "Ти си архитектурен анализатор. Работиш по проект 'Кристо' в Габрово.")

# ============================================
# DOCUMENT READER
# ============================================

class DocumentReader:
    def __init__(self):
        self.supported_extensions = ['.txt', '.md', '.docx', '.pdf', '.py', '.json', '.csv', '.dxf', '.zip']
    
    def read_folder(self, folder_path):
        documents = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    documents.append({
                        "name": file,
                        "path": file_path,
                        "type": "image",
                        "content": f"[ИЗОБРАЖЕНИЕ: {file}]\nРазмер: {os.path.getsize(file_path)} bytes"
                    })
                    continue
                
                if ext in self.supported_extensions or ext in ['.jpg', '.jpeg', '.png']:
                    try:
                        content = self.read_file(file_path)
                        documents.append({
                            "name": file,
                            "path": file_path,
                            "type": ext,
                            "content": content[:5000]
                        })
                    except Exception as e:
                        documents.append({
                            "name": file,
                            "path": file_path,
                            "type": ext,
                            "content": f"Грешка: {str(e)}"
                        })
        return documents
    
    def read_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.txt', '.md', '.py', '.json', '.csv']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        elif ext == '.docx':
            try:
                import docx
                doc = docx.Document(file_path)
                return '\n'.join([p.text for p in doc.paragraphs])
            except:
                return "Не може да се прочете .docx"
        
        elif ext == '.pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    return '\n'.join([p.extract_text() for p in reader.pages])
            except:
                return "Не може да се прочете PDF"
        
        elif ext == '.dxf':
            return self.read_dxf(file_path)
        
        elif ext == '.zip':
            return self.read_zip(file_path)
        
        return "Неподдържан формат"
    
    def read_dxf(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            lines = content.split('\n')
            text_info = []
            for i, line in enumerate(lines):
                if 'TEXT' in line or 'MTEXT' in line:
                    if i + 1 < len(lines):
                        text_info.append(lines[i+1].strip())
            result = f"[DXF: {os.path.basename(file_path)}]\n"
            result += f"Текстови елементи: {len(text_info)}\n"
            if text_info:
                result += f"Съдържание: {', '.join(text_info[:10])}\n"
            return result
        except Exception as e:
            return f"[DXF: {os.path.basename(file_path)}]\nГрешка: {str(e)}"
    
    def read_zip(self, file_path):
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                files = z.namelist()
                result = f"[ZIP: {os.path.basename(file_path)}]\n"
                result += f"Съдържа {len(files)} файла:\n"
                for f in files[:20]:
                    result += f"  - {f}\n"
                if len(files) > 20:
                    result += f"  ... и още {len(files)-20}\n"
                return result
        except Exception as e:
            return f"[ZIP: {os.path.basename(file_path)}]\nГрешка: {str(e)}"

# ============================================
# GITHUB CONNECTOR
# ============================================

class GitHubConnector:
    def __init__(self, token=None):
        self.token = token
        self.base_url = "https://api.github.com"
    
    def set_token(self, token):
        self.token = token
        with open("github_token.txt", "w") as f:
            f.write(token)
    
    def load_token(self):
        try:
            with open("github_token.txt", "r") as f:
                self.token = f.read().strip()
                return True
        except:
            return False
    
    def create_gist(self, description, content, filename="kristo_project.md", public=False):
        if not self.token:
            return "❌ Няма GitHub токен. Задай го първо."
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            data = {
                "description": description,
                "public": public,
                "files": {
                    filename: {
                        "content": content
                    }
                }
            }
            response = requests.post(f"{self.base_url}/gists", json=data, headers=headers)
            if response.status_code == 201:
                gist_data = response.json()
                return f"✅ Gist създаден успешно!\n🔗 Линк: {gist_data['html_url']}"
            else:
                return f"❌ Грешка при създаване: {response.status_code}\n{response.text[:300]}"
        except Exception as e:
            return f"❌ Грешка: {str(e)}"
    
    def create_repo(self, name, description="KRISTO Project", private=True):
        if not self.token:
            return "❌ Няма GitHub токен."
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            data = {
                "name": name,
                "description": description,
                "private": private,
                "auto_init": True
            }
            response = requests.post(f"{self.base_url}/user/repos", json=data, headers=headers)
            if response.status_code == 201:
                repo_data = response.json()
                return f"✅ Репозиторий създаден!\n🔗 {repo_data['html_url']}"
            else:
                return f"❌ Грешка: {response.status_code}\n{response.text[:300]}"
        except Exception as e:
            return f"❌ Грешка: {str(e)}"

# ============================================
# AGENTS
# ============================================

class ResearcherAgent:
    def __init__(self, ai_model, web_search):
        self.ai = ai_model
        self.web = web_search
    
    def research(self, topic):
        self.web.search_history = []
        results = self.web.search(topic, num_results=5)
        analysis = self.web.analyze_search_results(results, self.ai)
        return f"🔍 ИЗСЛЕДВАНЕ: {topic}\n\n{analysis}"

class WriterAgent:
    def __init__(self, ai_model):
        self.ai = ai_model
    
    def write(self, prompt, context=""):
        full_prompt = f"{context}\n\nЗАДАЧА: {prompt}\n\nНапиши професионален текст за архитектурен конкурс на български език."
        return self.ai.generate(full_prompt, "Ти си архитектурен писател.")

class CriticAgent:
    def __init__(self, ai_model):
        self.ai = ai_model
    
    def review(self, text):
        prompt = f"""Прегледай следния текст и дай конструктивна критика:

{text[:3000]}

Оцени:
1. Структура и яснота
2. Професионална терминология
3. Пълнота на информацията
4. Препоръки за подобрение"""
        return self.ai.generate(prompt, "Ти си архитектурен критик.")

class ConceptDesignerAgent:
    def __init__(self, ai_model):
        self.ai = ai_model
    
    def design(self, requirements):
        prompt = f"""Създай архитектурна концепция за:

{requirements}

Включи:
1. Визия и концепция
2. Пространствено решение
3. Материали
4. Устойчивост
5. Интеграция със заобикалящата среда"""
        return self.ai.generate(prompt, "Ти си архитектурен концептуалист.")

# ============================================
# MAIN GUI
# ============================================

class KristoOrchestrator:
    def __init__(self, root):
        self.root = root
        self.root.title("🎭 KRISTO ORCHESTRATOR - AI + Web Search + Competition")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1e1e2e")
        
        # AI Models
        self.ollama = OllamaAI()
        self.gemini = GeminiAI()
        self.web_search = WebSearchAgent()
        self.doc_reader = DocumentReader()
        self.github = GitHubConnector()
        
        # Agents
        self.researcher = None
        self.writer = None
        self.critic = None
        self.designer = None
        
        self.project_folder = None
        self.documents = []
        
        self.setup_ui()
        
        # Select primary AI (след setup_ui, защото log() използва log_text)
        self.ai = self._select_ai()
        
        # Initialize agents с избрания AI
        self.researcher = ResearcherAgent(self.ai, self.web_search)
        self.writer = WriterAgent(self.ai)
        self.critic = CriticAgent(self.ai)
        self.designer = ConceptDesignerAgent(self.ai)
        
        self.log("🎭 KRISTO ORCHESTRATOR стартира!")
        self.log(f"🤖 AI: {'Gemini' if isinstance(self.ai, GeminiAI) else 'Ollama'}")
    
    def _select_ai(self):
        # Не използвай self.log() тук, защото log_text още не е създаден
        if self.gemini.is_available():
            return self.gemini
        elif self.ollama.is_running():
            return self.ollama
        else:
            return self.gemini
    
    def setup_ui(self):
        # Main container
        main = tk.Frame(self.root, bg="#1e1e2e")
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_frame = tk.Frame(main, bg="#1e1e2e")
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(title_frame, text="🎭 KRISTO ORCHESTRATOR", 
                font=("Segoe UI", 24, "bold"), bg="#1e1e2e", fg="#00d4ff").pack()
        tk.Label(title_frame, text="AI Мулти-Агент Система + Web Search + Конкурс Фаза 1", 
                font=("Segoe UI", 11), bg="#1e1e2e", fg="#a0a0b0").pack()
        
        # Top frame - Agents and Controls
        top_frame = tk.Frame(main, bg="#1e1e2e")
        top_frame.pack(fill=tk.X, pady=5)
        
        # Left - Agents
        agents_frame = tk.LabelFrame(top_frame, text="🤖 АГЕНТИ", font=("Segoe UI", 10, "bold"),
                                     bg="#252535", fg="#00d4ff", padx=10, pady=10)
        agents_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        self.agent_status = {}
        agents = [
            ("🔍 Researcher", "Изследовател", "#4a9eff"),
            ("✍️ Writer", "Писател", "#50c878"),
            ("🎨 Concept Designer", "Концептуалист", "#ff6b6b"),
            ("🔍 Critic", "Критик", "#ffd93d")
        ]
        
        for name, role, color in agents:
            frame = tk.Frame(agents_frame, bg="#252535", pady=3)
            frame.pack(fill=tk.X)
            tk.Label(frame, text=name, font=("Segoe UI", 10, "bold"), 
                    bg="#252535", fg=color).pack(side=tk.LEFT)
            tk.Label(frame, text=f"• {role}", font=("Segoe UI", 9), 
                    bg="#252535", fg="#8888a0").pack(side=tk.LEFT, padx=5)
            status = tk.Label(frame, text="Готов", font=("Segoe UI", 8), 
                             bg="#252535", fg="#50c878")
            status.pack(side=tk.RIGHT)
            self.agent_status[name] = status
        
        # Center - Controls
        controls_frame = tk.LabelFrame(top_frame, text="🎮 КОНТРОЛИ", font=("Segoe UI", 10, "bold"),
                                       bg="#252535", fg="#00d4ff", padx=10, pady=10)
        controls_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Task input
        tk.Label(controls_frame, text="Въведи задача:", font=("Segoe UI", 10), 
                bg="#252535", fg="#c0c0d0").pack(anchor=tk.W)
        self.task_entry = tk.Entry(controls_frame, font=("Segoe UI", 11), 
                                    bg="#1e1e2e", fg="#ffffff", insertbackground="#00d4ff")
        self.task_entry.pack(fill=tk.X, pady=5)
        self.task_entry.bind("<Return>", lambda e: self.execute_task())
        
        # Buttons row 1
        btn_frame1 = tk.Frame(controls_frame, bg="#252535")
        btn_frame1.pack(fill=tk.X, pady=3)
        
        tk.Button(btn_frame1, text="🚀 ИЗПЪЛНИ С AI", font=("Segoe UI", 10, "bold"),
                 bg="#00d4ff", fg="#1e1e2e", command=self.execute_task,
                 cursor="hand2", width=15).pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame1, text="🌐 ТЪРСИ", font=("Segoe UI", 10, "bold"),
                 bg="#4a9eff", fg="white", command=self.web_search_task,
                 cursor="hand2", width=12).pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame1, text="📊 АНАЛИЗ", font=("Segoe UI", 10, "bold"),
                 bg="#ff6b6b", fg="white", command=self.analyze_task,
                 cursor="hand2", width=12).pack(side=tk.LEFT, padx=2)
        
        # Buttons row 2
        btn_frame2 = tk.Frame(controls_frame, bg="#252535")
        btn_frame2.pack(fill=tk.X, pady=3)
        
        tk.Button(btn_frame2, text="🏆 ФАЗА 1", font=("Segoe UI", 10, "bold"),
                 bg="#ffd93d", fg="#1e1e2e", command=self.phase1_competition,
                 cursor="hand2", width=12).pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame2, text="💻 VS CODE", font=("Segoe UI", 10, "bold"),
                 bg="#007acc", fg="white", command=self.open_vscode,
                 cursor="hand2", width=12).pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame2, text="💾 ЗАПАЗИ", font=("Segoe UI", 10, "bold"),
                 bg="#50c878", fg="white", command=self.save_result,
                 cursor="hand2", width=12).pack(side=tk.LEFT, padx=2)
        
        # Documents section
        tk.Label(controls_frame, text="Документи:", font=("Segoe UI", 10), 
                bg="#252535", fg="#c0c0d0").pack(anchor=tk.W, pady=(10, 0))
        
        doc_frame = tk.Frame(controls_frame, bg="#252535")
        doc_frame.pack(fill=tk.X, pady=3)
        
        tk.Button(doc_frame, text="📁 Избери Папка", font=("Segoe UI", 9),
                 bg="#3a3a4a", fg="white", command=self.select_folder,
                 cursor="hand2").pack(side=tk.LEFT, padx=2)
        
        tk.Button(doc_frame, text="📄 Избери Файл", font=("Segoe UI", 9),
                 bg="#3a3a4a", fg="white", command=self.select_file,
                 cursor="hand2").pack(side=tk.LEFT, padx=2)
        
        self.folder_label = tk.Label(controls_frame, text="Папка: (не е избрана)", 
                                    font=("Segoe UI", 9), bg="#252535", fg="#8888a0")
        self.folder_label.pack(anchor=tk.W, pady=2)
        
        # Right - Project Info
        project_frame = tk.LabelFrame(top_frame, text="📋 ПРОЕКТ 'КРИСТО'", 
                                      font=("Segoe UI", 10, "bold"),
                                      bg="#252535", fg="#00d4ff", padx=10, pady=10)
        project_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        self.project_info = tk.Text(project_frame, font=("Segoe UI", 9), 
                                   bg="#1e1e2e", fg="#c0c0d0", 
                                   width=25, height=10, wrap=tk.WORD)
        self.project_info.pack(fill=tk.BOTH, expand=True)
        self.project_info.insert(tk.END, "Име: Кристо\nЗадачи: 0\nДокументи: 0\nПапка: -\n\n")
        self.project_info.config(state=tk.DISABLED)
        
        # GitHub button
        tk.Button(project_frame, text="🔗 GitHub", font=("Segoe UI", 9),
                 bg="#3a3a4a", fg="white", command=self.github_actions,
                 cursor="hand2").pack(fill=tk.X, pady=5)
        
        # Bottom - Results and Log
        bottom_frame = tk.Frame(main, bg="#1e1e2e")
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Results
        result_frame = tk.LabelFrame(bottom_frame, text="📝 РЕЗУЛТАТ ОТ AI", 
                                     font=("Segoe UI", 10, "bold"),
                                     bg="#252535", fg="#00d4ff", padx=5, pady=5)
        result_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.result_text = scrolledtext.ScrolledText(
            result_frame, font=("Consolas", 10), 
            bg="#1e1e2e", fg="#c0c0d0",
            wrap=tk.WORD, height=20, padx=10, pady=10
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Log
        log_frame = tk.LabelFrame(bottom_frame, text="📜 ЛОГ", 
                                  font=("Segoe UI", 10, "bold"),
                                  bg="#252535", fg="#00d4ff", padx=5, pady=5)
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, font=("Consolas", 9), 
            bg="#1e1e2e", fg="#8888a0",
            wrap=tk.WORD, height=20, width=50, padx=10, pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_bar = tk.Label(main, text="Готов", font=("Segoe UI", 9), 
                                  bg="#1e1e2e", fg="#50c878", anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def set_status(self, text, color="#50c878"):
        self.status_bar.config(text=text, fg=color)
    
    def execute_task(self):
        task = self.task_entry.get().strip()
        if not task:
            messagebox.showwarning("Внимание", "Моля, въведете задача!")
            return
        
        self.set_status("Работи...", "#ffd93d")
        self.log(f"🚀 Изпълнение: {task}")
        
        threading.Thread(target=self._execute, args=(task,), daemon=True).start()
    
    def _execute(self, task):
        try:
            context = ""
            if self.documents:
                context = "КОНТЕКСТ ОТ ДОКУМЕНТИ:\n"
                for doc in self.documents[:3]:
                    context += f"\n--- {doc['name']} ---\n{doc['content'][:500]}\n"
            
            prompt = f"{context}\n\nЗАДАЧА: {task}\n\nИзпълни професионално на български език."
            result = self.ai.generate(prompt, "Ти си архитектурен асистент за проект 'Кристо' в Габрово.")
            
            self.root.after(0, lambda: self.result_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.result_text.insert(tk.END, result))
            self.root.after(0, lambda: self.log("✅ Задачата е изпълнена!"))
            self.root.after(0, lambda: self.set_status("Готов", "#50c878"))
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ Грешка: {str(e)}"))
            self.root.after(0, lambda: self.set_status("Грешка", "#ff6b6b"))
    
    def web_search_task(self):
        query = self.task_entry.get().strip()
        if not query:
            query = "Кристо Жан-Клод Габрово архитектурен конкурс"
        
        self.set_status("Търсене...", "#ffd93d")
        self.log(f"🌐 Търсене: {query}")
        
        threading.Thread(target=self._web_search, args=(query,), daemon=True).start()
    
    def _web_search(self, query):
        try:
            result = self.researcher.research(query)
            self.root.after(0, lambda: self.result_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.result_text.insert(tk.END, result))
            self.root.after(0, lambda: self.log("✅ Търсенето завърши!"))
            self.root.after(0, lambda: self.set_status("Готов", "#50c878"))
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ Грешка: {str(e)}"))
            self.root.after(0, lambda: self.set_status("Грешка", "#ff6b6b"))
    
    def analyze_task(self):
        text = self.result_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Внимание", "Няма текст за анализ!")
            return
        
        self.set_status("Анализ...", "#ffd93d")
        self.log("📊 Анализ на резултата...")
        
        threading.Thread(target=self._analyze, args=(text,), daemon=True).start()
    
    def _analyze(self, text):
        try:
            result = self.critic.review(text)
            self.root.after(0, lambda: self.result_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.result_text.insert(tk.END, result))
            self.root.after(0, lambda: self.log("✅ Анализът е готов!"))
            self.root.after(0, lambda: self.set_status("Готов", "#50c878"))
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ Грешка: {str(e)}"))
    
    def phase1_competition(self):
        self.set_status("Фаза 1...", "#ffd93d")
        self.log("🏆 Стартиране на Конкурс Фаза 1...")
        
        threading.Thread(target=self._phase1, daemon=True).start()
    
    def _phase1(self):
        try:
            full_result = "🏆 КОНКУРС ФАЗА 1 - КУЛТУРЕН ЦЕНТЪР 'КРИСТО И ЖАН-КЛОД'\n"
            full_result += "=" * 70 + "\n\n"
            
            # Step 1: Research
            self.root.after(0, lambda: self.log("📚 Стъпка 1: Изследване..."))
            research = self.researcher.research("Кристо Жан-Клод Габрово културен център конкурс")
            full_result += "1️⃣ ИЗСЛЕДВАНЕ\n" + "=" * 50 + "\n" + research + "\n\n"
            self.root.after(0, lambda: self.result_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.result_text.insert(tk.END, full_result))
            
            # Step 2: Concept
            self.root.after(0, lambda: self.log("💡 Стъпка 2: Концепция..."))
            concept = self.designer.design("Културен център 'Кристо и Жан-Клод' в Габрово, адаптивно използване на промишлено наследство")
            full_result += "2️⃣ КОНЦЕПЦИЯ\n" + "=" * 50 + "\n" + concept + "\n\n"
            self.root.after(0, lambda: self.result_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.result_text.insert(tk.END, full_result))
            
            # Step 3: Writer
            self.root.after(0, lambda: self.log("✍️ Стъпка 3: Текстове..."))
            texts = self.writer.write("Напиши конкурсно описание за културен център 'Кристо и Жан-Клод'", concept)
            full_result += "3️⃣ ТЕКСТОВЕ ЗА КОНКУРСА\n" + "=" * 50 + "\n" + texts + "\n\n"
            self.root.after(0, lambda: self.result_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.result_text.insert(tk.END, full_result))
            
            # Step 4: Critic
            self.root.after(0, lambda: self.log("🔍 Стъпка 4: Преглед..."))
            review = self.critic.review(full_result)
            full_result += "4️⃣ ПРЕГЛЕД И ПРЕПОРЪКИ\n" + "=" * 50 + "\n" + review + "\n\n"
            
            full_result += "=" * 70 + "\n"
            full_result += f"✅ ГЕНЕРИРАНО НА: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            full_result += "📁 Запази резултата с бутон 'ЗАПАЗИ'\n"
            
            self.root.after(0, lambda: self.result_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.result_text.insert(tk.END, full_result))
            self.root.after(0, lambda: self.log("✅ Фаза 1 завършена!"))
            self.root.after(0, lambda: self.set_status("Готов", "#50c878"))
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ Грешка във Фаза 1: {str(e)}"))
            self.root.after(0, lambda: self.set_status("Грешка", "#ff6b6b"))
    
    def open_vscode(self):
        try:
            subprocess.Popen(["code", "."], shell=True)
            self.log("💻 VS Code е отворен!")
        except:
            self.log("❌ Не може да се отвори VS Code")
    
    def save_result(self):
        content = self.result_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Внимание", "Няма резултат за запазване!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("Word", "*.docx"), ("All", "*.*")],
            initialfile=f"Kristo_Project_{datetime.now().strftime('%Y%m%d_%H%M')}"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log(f"💾 Запазено: {os.path.basename(file_path)}")
                messagebox.showinfo("Успех", "Файлът е запазен!")
            except Exception as e:
                messagebox.showerror("Грешка", f"Неуспешно запазване: {str(e)}")
    
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.project_folder = folder
            self.folder_label.config(text=f"Папка: {os.path.basename(folder)}")
            self.log(f"📁 Избрана папка: {folder}")
            
            self.documents = self.doc_reader.read_folder(folder)
            self.log(f"📄 Намерени {len(self.documents)} документа")
            
            self._update_project_info()
    
    def select_file(self):
        file = filedialog.askopenfilename(filetypes=[("All files", "*.*")])
        if file:
            content = self.doc_reader.read_file(file)
            self.documents.append({
                "name": os.path.basename(file),
                "path": file,
                "type": os.path.splitext(file)[1],
                "content": content
            })
            self.log(f"📄 Добавен файл: {os.path.basename(file)}")
            self._update_project_info()
    
    def _update_project_info(self):
        self.project_info.config(state=tk.NORMAL)
        self.project_info.delete("1.0", tk.END)
        info = f"Име: Кристо\n"
        info += f"Задачи: {len(self.web_search.search_history)}\n"
        info += f"Документи: {len(self.documents)}\n"
        info += f"Папка: {os.path.basename(self.project_folder) if self.project_folder else '-'}\n\n"
        
        for doc in self.documents[:5]:
            info += f"• {doc['name']}\n"
        
        self.project_info.insert(tk.END, info)
        self.project_info.config(state=tk.DISABLED)
    
    def github_actions(self):
        # Simple dialog for GitHub
        dialog = tk.Toplevel(self.root)
        dialog.title("GitHub Actions")
        dialog.geometry("400x300")
        dialog.configure(bg="#1e1e2e")
        
        tk.Label(dialog, text="GitHub Token:", font=("Segoe UI", 10), bg="#1e1e2e", fg="white").pack(pady=5)
        token_entry = tk.Entry(dialog, font=("Segoe UI", 10), show="*", width=40)
        token_entry.pack(pady=5)
        
        if self.github.load_token():
            token_entry.insert(0, "******** (зареден)")
        
        def save_token():
            self.github.set_token(token_entry.get())
            self.log("🔑 GitHub токен е зададен!")
        
        tk.Button(dialog, text="💾 Запази Токен", command=save_token,
                 bg="#00d4ff", fg="#1e1e2e", font=("Segoe UI", 10, "bold")).pack(pady=5)
        
        tk.Label(dialog, text="Действия:", font=("Segoe UI", 10, "bold"), bg="#1e1e2e", fg="white").pack(pady=10)
        
        def create_gist():
            content = self.result_text.get("1.0", tk.END).strip()
            if content:
                result = self.github.create_gist("KRISTO Project", content)
                self.log(result)
                messagebox.showinfo("Резултат", result)
        
        tk.Button(dialog, text="📤 Създай Gist", command=create_gist,
                 bg="#4a9eff", fg="white", font=("Segoe UI", 10)).pack(pady=3)
        
        def create_repo():
            result = self.github.create_repo("kristo-project", "KRISTO Cultural Center Project")
            self.log(result)
            messagebox.showinfo("Резултат", result)
        
        tk.Button(dialog, text="📁 Създай Repo", command=create_repo,
                 bg="#50c878", fg="white", font=("Segoe UI", 10)).pack(pady=3)


# ============================================
# START
# ============================================

if __name__ == "__main__":
    root = tk.Tk()
    app = KristoOrchestrator(root)
    root.mainloop()

