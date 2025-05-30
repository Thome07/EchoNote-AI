import os
import csv
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import requests
import re
from pathlib import Path
from datetime import datetime
import hashlib

class ObsidianAIManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Obsidian AI Manager - Sistema de Anotações Inteligente")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Configuração de cores e estilo
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'accent': '#007acc',
            'secondary': '#2d2d2d',
            'success': '#28a745',
            'error': '#dc3545',
            'warning': '#ffc107'
        }
        
        self.configure_style()
        
        # Variáveis
        self.api_key = tk.StringVar()
        self.status_var = tk.StringVar(value="Pronto para usar")
        self.notes_data = []
        self.config_file = "obsidian_config.json"
        self.csv_file = "obsidian_notes.csv"
        self.obsidian_path = r"C:\Users\igort\OneDrive\Obsidian"
        
        # Carregar configurações
        self.load_config()
        
        # Criar interface
        self.create_interface()
        
        # Verificar se há notas para carregar
        self.check_and_load_notes()
    
    def configure_style(self):
        """Configura o estilo visual da aplicação"""
        self.root.configure(bg=self.colors['bg'])
        
        # Configurar ttk style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar cores para widgets ttk
        style.configure('Custom.TFrame', background=self.colors['bg'])
        style.configure('Custom.TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('Custom.TButton', background=self.colors['accent'], foreground='white')
        style.configure('Custom.TEntry', fieldbackground=self.colors['secondary'], foreground=self.colors['fg'])
    
    def create_interface(self):
        """Cria a interface gráfica principal"""
        # Frame principal
        main_frame = ttk.Frame(self.root, style='Custom.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Criar notebook para abas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Aba principal - Chat com IA
        self.create_chat_tab()
        
        # Aba de configurações
        self.create_config_tab()
        
        # Aba de gerenciamento de notas
        self.create_notes_tab()
        
        # Barra de status
        self.create_status_bar(main_frame)
    
    def create_chat_tab(self):
        """Cria a aba principal do chat com IA"""
        chat_frame = ttk.Frame(self.notebook, style='Custom.TFrame')
        self.notebook.add(chat_frame, text="💬 Chat com IA")
        
        # Frame superior - histórico do chat
        history_frame = ttk.LabelFrame(chat_frame, text="Conversa com IA", style='Custom.TFrame')
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.chat_history = scrolledtext.ScrolledText(
            history_frame,
            wrap=tk.WORD,
            bg=self.colors['secondary'],
            fg=self.colors['fg'],
            font=('Consolas', 11),
            insertbackground=self.colors['fg']
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configurar tags para formatação
        self.chat_history.tag_configure("user", foreground="#4CAF50", font=('Consolas', 11, 'bold'))
        self.chat_history.tag_configure("ai", foreground="#2196F3", font=('Consolas', 11, 'bold'))
        self.chat_history.tag_configure("system", foreground="#FF9800", font=('Consolas', 10, 'italic'))
        self.chat_history.tag_configure("reference", foreground="#9C27B0", font=('Consolas', 10))
        
        # Tags para formatação Markdown
        self.chat_history.tag_configure("bold", font=('Consolas', 11, 'bold'))
        self.chat_history.tag_configure("italic", font=('Consolas', 11, 'italic'))
        self.chat_history.tag_configure("code", font=('Courier', 10), background="#3a3a3a", foreground="#f8f8f2")
        self.chat_history.tag_configure("code_block", font=('Courier', 10), background="#2d2d2d", foreground="#f8f8f2")
        self.chat_history.tag_configure("heading1", font=('Consolas', 14, 'bold'), foreground="#ffffff")
        self.chat_history.tag_configure("heading2", font=('Consolas', 13, 'bold'), foreground="#e0e0e0")
        self.chat_history.tag_configure("heading3", font=('Consolas', 12, 'bold'), foreground="#d0d0d0")
        self.chat_history.tag_configure("quote", font=('Consolas', 10, 'italic'), foreground="#b0b0b0", lmargin1=20)
        self.chat_history.tag_configure("link", foreground="#66d9ff", underline=True)
        
        # Frame inferior - entrada de mensagem
        input_frame = ttk.LabelFrame(chat_frame, text="Sua mensagem", style='Custom.TFrame')
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Campo de entrada de texto
        self.message_entry = tk.Text(
            input_frame,
            height=3,
            wrap=tk.WORD,
            bg=self.colors['secondary'],
            fg=self.colors['fg'],
            font=('Consolas', 11),
            insertbackground=self.colors['fg']
        )
        self.message_entry.pack(fill=tk.X, padx=5, pady=5)
        
        # Binds para teclas
        self.message_entry.bind('<Return>', self.handle_enter)
        self.message_entry.bind('<Control-Return>', self.insert_newline)
        
        # Frame para botões
        button_frame = ttk.Frame(input_frame, style='Custom.TFrame')
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Botão enviar
        send_btn = ttk.Button(
            button_frame,
            text="📤 Enviar (Enter)",
            command=self.send_message,
            style='Custom.TButton'
        )
        send_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botão limpar chat
        clear_btn = ttk.Button(
            button_frame,
            text="🗑️ Limpar Chat",
            command=self.clear_chat,
            style='Custom.TButton'
        )
        clear_btn.pack(side=tk.LEFT)
        
        # Label com instruções
        instruction_label = ttk.Label(
            button_frame,
            text="💡 Dica: Use Ctrl+Enter para nova linha, Enter para enviar",
            style='Custom.TLabel',
            font=('Arial', 9)
        )
        instruction_label.pack(side=tk.RIGHT)
    
    def create_config_tab(self):
        """Cria a aba de configurações"""
        config_frame = ttk.Frame(self.notebook, style='Custom.TFrame')
        self.notebook.add(config_frame, text="⚙️ Configurações")
        
        # Frame da API
        api_frame = ttk.LabelFrame(config_frame, text="Configuração da API Gemini", style='Custom.TFrame')
        api_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(api_frame, text="Chave da API:", style='Custom.TLabel').pack(anchor=tk.W, padx=5, pady=5)
        
        api_entry_frame = ttk.Frame(api_frame, style='Custom.TFrame')
        api_entry_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.api_entry = ttk.Entry(
            api_entry_frame,
            textvariable=self.api_key,
            show="*",
            style='Custom.TEntry',
            font=('Consolas', 10)
        )
        self.api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        save_api_btn = ttk.Button(
            api_entry_frame,
            text="💾 Salvar",
            command=self.save_api_key,
            style='Custom.TButton'
        )
        save_api_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Frame do diretório Obsidian
        dir_frame = ttk.LabelFrame(config_frame, text="Diretório do Obsidian", style='Custom.TFrame')
        dir_frame.pack(fill=tk.X, padx=10, pady=10)
        
        dir_entry_frame = ttk.Frame(dir_frame, style='Custom.TFrame')
        dir_entry_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.dir_var = tk.StringVar(value=self.obsidian_path)
        dir_entry = ttk.Entry(
            dir_entry_frame,
            textvariable=self.dir_var,
            style='Custom.TEntry',
            font=('Consolas', 10)
        )
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(
            dir_entry_frame,
            text="📂 Procurar",
            command=self.browse_directory,
            style='Custom.TButton'
        )
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Frame de ações
        actions_frame = ttk.LabelFrame(config_frame, text="Ações", style='Custom.TFrame')
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        actions_button_frame = ttk.Frame(actions_frame, style='Custom.TFrame')
        actions_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        scan_btn = ttk.Button(
            actions_button_frame,
            text="🔍 Escanear Notas",
            command=self.scan_notes_threaded,
            style='Custom.TButton'
        )
        scan_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        test_api_btn = ttk.Button(
            actions_button_frame,
            text="🧪 Testar API",
            command=self.test_api_connection,
            style='Custom.TButton'
        )
        test_api_btn.pack(side=tk.LEFT)
    
    def create_notes_tab(self):
        """Cria a aba de gerenciamento de notas"""
        notes_frame = ttk.Frame(self.notebook, style='Custom.TFrame')
        self.notebook.add(notes_frame, text="📝 Notas")
        
        # Frame de informações
        info_frame = ttk.LabelFrame(notes_frame, text="Informações das Notas", style='Custom.TFrame')
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.notes_info_label = ttk.Label(
            info_frame,
            text="Nenhuma nota carregada",
            style='Custom.TLabel',
            font=('Arial', 10)
        )
        self.notes_info_label.pack(padx=5, pady=5)
        
        # Lista de notas
        list_frame = ttk.LabelFrame(notes_frame, text="Lista de Notas", style='Custom.TFrame')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview para mostrar as notas
        columns = ('título', 'caminho', 'tamanho', 'modificação')
        self.notes_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configurar colunas
        self.notes_tree.heading('título', text='Título')
        self.notes_tree.heading('caminho', text='Caminho')
        self.notes_tree.heading('tamanho', text='Tamanho')
        self.notes_tree.heading('modificação', text='Última Modificação')
        
        self.notes_tree.column('título', width=200)
        self.notes_tree.column('caminho', width=300)
        self.notes_tree.column('tamanho', width=100)
        self.notes_tree.column('modificação', width=150)
        
        # Scrollbar para a lista
        notes_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.notes_tree.yview)
        self.notes_tree.configure(yscrollcommand=notes_scrollbar.set)
        
        self.notes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        notes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_status_bar(self, parent):
        """Cria a barra de status"""
        status_frame = ttk.Frame(parent, style='Custom.TFrame')
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            style='Custom.TLabel',
            font=('Arial', 9)
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Progressbar
        self.progress = ttk.Progressbar(
            status_frame,
            mode='indeterminate'
        )
        self.progress.pack(side=tk.RIGHT, padx=(10, 0))
    
    def handle_enter(self, event):
        """Manipula o pressionamento da tecla Enter"""
        self.send_message()
        return 'break'
    
    def insert_newline(self, event):
        """Insere uma nova linha com Ctrl+Enter"""
        self.message_entry.insert(tk.INSERT, '\n')
        return 'break'
    
    def send_message(self):
        """Envia mensagem para a IA"""
        message = self.message_entry.get(1.0, tk.END).strip()
        if not message:
            return
        
        if not self.api_key.get():
            messagebox.showwarning("Aviso", "Por favor, configure a chave da API primeiro!")
            self.notebook.select(1)  # Ir para aba de configurações
            return
        
        if not self.notes_data:
            messagebox.showwarning("Aviso", "Nenhuma nota foi carregada. Por favor, escaneie as notas primeiro!")
            return
        
        # Limpar campo de entrada
        self.message_entry.delete(1.0, tk.END)
        
        # Adicionar mensagem do usuário ao chat
        self.add_to_chat("Você", message, "user")
        
        # Enviar para IA em thread separada
        threading.Thread(target=self.process_ai_request, args=(message,), daemon=True).start()
    
    def process_ai_request(self, message):
        """Processa a requisição para a IA"""
        try:
            self.update_status("Processando mensagem...")
            self.progress.start()
            
            # Preparar contexto das notas
            context = self.prepare_context(message)
            
            # Fazer requisição para API
            response = self.call_gemini_api(message, context)
            
            # Adicionar resposta ao chat
            self.root.after(0, self.add_to_chat, "IA", response, "ai")
            
        except Exception as e:
            error_msg = f"Erro ao processar mensagem: {str(e)}"
            self.root.after(0, self.add_to_chat, "Sistema", error_msg, "system")
        finally:
            self.root.after(0, self.progress.stop)
            self.root.after(0, self.update_status, "Pronto para usar")
    
    def prepare_context(self, user_message):
        """Prepara o contexto das notas para enviar à IA"""
        # Buscar notas relevantes baseadas na mensagem do usuário
        relevant_notes = self.find_relevant_notes(user_message)
        
        context = "Base de conhecimento das suas anotações:\n\n"
        
        for note in relevant_notes[:5]:  # Limitar a 5 notas mais relevantes
            context += f"=== {note['título']} ===\n"
            context += f"Arquivo: {note['caminho']}\n"
            context += f"Conteúdo: {note['conteúdo'][:1000]}...\n\n"  # Limitar conteúdo
        
        return context
    
    def find_relevant_notes(self, query):
        """Encontra notas relevantes baseadas na consulta"""
        query_lower = query.lower()
        scored_notes = []
        
        for note in self.notes_data:
            score = 0
            title_lower = note['título'].lower()
            content_lower = note['conteúdo'].lower()
            
            # Pontuação baseada em palavras-chave no título
            for word in query_lower.split():
                if word in title_lower:
                    score += 3
                if word in content_lower:
                    score += 1
            
            if score > 0:
                scored_notes.append((score, note))
        
        # Ordenar por pontuação e retornar apenas as notas
        scored_notes.sort(key=lambda x: x[0], reverse=True)
        return [note for score, note in scored_notes]
    
    def call_gemini_api(self, message, context):
        """Faz chamada para a API do Gemini"""
        api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        prompt = f"""Você é um assistente inteligente especializado em ajudar com anotações pessoais do Obsidian.

Sua tarefa é responder perguntas sobre o conteúdo das anotações, indicando sempre em qual arquivo a informação foi encontrada.

**IMPORTANTE:** Use formatação Markdown em suas respostas para melhor legibilidade:
- Use **negrito** para destacar informações importantes
- Use *itálico* para ênfase
- Use `código` para nomes de arquivos, funções, variáveis
- Use ### para subtítulos
- Use > para citações importantes
- Use listas quando apropriado

{context}

**Pergunta do usuário:** {message}

Por favor, responda de forma clara e útil, sempre mencionando as fontes (nomes dos arquivos) quando referenciar informações específicas das anotações. Use formatação Markdown para tornar sua resposta mais legível e organizada."""

        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(
            f"{api_url}?key={self.api_key.get()}",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            raise Exception(f"Erro na API: {response.status_code} - {response.text}")
    
    def add_to_chat(self, sender, message, tag):
        """Adiciona mensagem ao histórico do chat com suporte a Markdown"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.chat_history.insert(tk.END, f"[{timestamp}] {sender}:\n", tag)
        
        # Se for mensagem da IA, aplicar formatação Markdown
        if tag == "ai":
            self.insert_markdown_text(message)
        else:
            self.chat_history.insert(tk.END, f"{message}\n\n")
        
        # Auto-scroll para o final
        self.chat_history.see(tk.END)
        
        # Focar no campo de entrada
        self.message_entry.focus_set()
    
    def insert_markdown_text(self, text):
        """Insere texto com formatação Markdown no chat"""
        import re
        
        lines = text.split('\n')
        
        for line in lines:
            # Verificar se é um cabeçalho
            if line.startswith('### '):
                self.chat_history.insert(tk.END, line[4:] + '\n', 'heading3')
            elif line.startswith('## '):
                self.chat_history.insert(tk.END, line[3:] + '\n', 'heading2')
            elif line.startswith('# '):
                self.chat_history.insert(tk.END, line[2:] + '\n', 'heading1')
            elif line.startswith('> '):
                # Citação
                self.chat_history.insert(tk.END, line[2:] + '\n', 'quote')
            elif line.strip().startswith('```') and line.strip().endswith('```'):
                # Bloco de código inline simples
                code_content = line.strip()[3:-3]
                self.chat_history.insert(tk.END, code_content + '\n', 'code_block')
            elif '```' in line:
                # Início ou fim de bloco de código
                if line.strip() == '```':
                    self.chat_history.insert(tk.END, '\n')
                else:
                    # Código com linguagem especificada
                    self.chat_history.insert(tk.END, line + '\n', 'code_block')
            else:
                # Processar formatação inline
                self.process_inline_formatting(line + '\n')
    
    def process_inline_formatting(self, text):
        """Processa formatação inline como negrito, itálico, código"""
        import re
        
        # Lista para armazenar segmentos de texto e suas formatações
        segments = []
        current_pos = 0
        
        # Padrões de formatação
        patterns = [
            (r'\*\*(.*?)\*\*', 'bold'),      # **texto**
            (r'\*(.*?)\*', 'italic'),        # *texto*
            (r'`(.*?)`', 'code'),            # `código`
            (r'\[(.*?)\]\((.*?)\)', 'link'), # [texto](link)
        ]
        
        # Encontrar todas as formatações
        all_matches = []
        for pattern, tag in patterns:
            for match in re.finditer(pattern, text):
                all_matches.append((match.start(), match.end(), match, tag))
        
        # Ordenar por posição
        all_matches.sort(key=lambda x: x[0])
        
        # Processar texto
        last_end = 0
        
        for start, end, match, tag in all_matches:
            # Adicionar texto normal antes da formatação
            if start > last_end:
                normal_text = text[last_end:start]
                if normal_text:
                    self.chat_history.insert(tk.END, normal_text)
            
            # Adicionar texto formatado
            if tag == 'link':
                # Para links, usar apenas o texto do link
                link_text = match.group(1)
                self.chat_history.insert(tk.END, link_text, tag)
            else:
                # Para outras formatações, usar o conteúdo capturado
                formatted_text = match.group(1)
                self.chat_history.insert(tk.END, formatted_text, tag)
            
            last_end = end
        
        # Adicionar texto restante
        if last_end < len(text):
            remaining_text = text[last_end:]
            self.chat_history.insert(tk.END, remaining_text)
    
    def clear_chat(self):
        """Limpa o histórico do chat"""
        self.chat_history.delete(1.0, tk.END)
    
    def scan_notes_threaded(self):
        """Executa escaneamento de notas em thread separada"""
        threading.Thread(target=self.scan_notes, daemon=True).start()
    
    def scan_notes(self):
        """Escaneia e processa todas as notas Markdown"""
        try:
            self.root.after(0, self.update_status, "Escaneando notas...")
            self.root.after(0, self.progress.start)
            
            obsidian_path = Path(self.dir_var.get())
            
            if not obsidian_path.exists():
                raise Exception(f"Diretório não encontrado: {obsidian_path}")
            
            notes = []
            
            # Buscar todos os arquivos .md, ignorando a pasta .obsidian
            for md_file in obsidian_path.rglob("*.md"):
                if ".obsidian" in str(md_file):
                    continue
                
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    title = md_file.stem
                    relative_path = str(md_file.relative_to(obsidian_path))
                    
                    # Estatísticas do arquivo
                    stat = md_file.stat()
                    size = self.format_file_size(stat.st_size)
                    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    
                    notes.append({
                        'título': title,
                        'conteúdo': content,
                        'caminho': relative_path,
                        'tamanho': size,
                        'modificação': modified,
                        'caminho_completo': str(md_file)
                    })
                    
                except Exception as e:
                    print(f"Erro ao ler arquivo {md_file}: {e}")
            
            # Salvar em CSV
            self.save_notes_to_csv(notes)
            
            # Atualizar dados e interface
            self.notes_data = notes
            self.root.after(0, self.update_notes_display)
            self.root.after(0, self.update_status, f"✅ {len(notes)} notas carregadas com sucesso!")
            
        except Exception as e:
            error_msg = f"Erro ao escanear notas: {str(e)}"
            self.root.after(0, self.update_status, f"❌ {error_msg}")
            self.root.after(0, messagebox.showerror, "Erro", error_msg)
        finally:
            self.root.after(0, self.progress.stop)
    
    def save_notes_to_csv(self, notes):
        """Salva as notas em um arquivo CSV"""
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['título', 'conteúdo', 'caminho', 'tamanho', 'modificação']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for note in notes:
                writer.writerow({
                    'título': note['título'],
                    'conteúdo': note['conteúdo'],
                    'caminho': note['caminho'],
                    'tamanho': note['tamanho'],
                    'modificação': note['modificação']
                })
    
    def update_notes_display(self):
        """Atualiza a exibição das notas na interface"""
        # Limpar lista atual
        for item in self.notes_tree.get_children():
            self.notes_tree.delete(item)
        
        # Adicionar notas
        for note in self.notes_data:
            self.notes_tree.insert('', tk.END, values=(
                note['título'],
                note['caminho'],
                note['tamanho'],
                note['modificação']
            ))
        
        # Atualizar informações
        total_notes = len(self.notes_data)
        total_chars = sum(len(note['conteúdo']) for note in self.notes_data)
        
        info_text = f"📊 Total: {total_notes} notas | {self.format_file_size(total_chars)} de conteúdo"
        self.notes_info_label.config(text=info_text)
    
    def format_file_size(self, size_bytes):
        """Formata o tamanho do arquivo em formato legível"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        else:
            return f"{size_bytes/(1024**2):.1f} MB"
    
    def check_and_load_notes(self):
        """Verifica se existe CSV de notas e carrega"""
        if os.path.exists(self.csv_file):
            threading.Thread(target=self.load_notes_from_csv, daemon=True).start()
    
    def load_notes_from_csv(self):
        """Carrega notas do arquivo CSV"""
        try:
            notes = []
            with open(self.csv_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    notes.append(row)
            
            self.notes_data = notes
            self.root.after(0, self.update_notes_display)
            self.root.after(0, self.update_status, f"✅ {len(notes)} notas carregadas do arquivo existente")
            
        except Exception as e:
            print(f"Erro ao carregar CSV: {e}")
    
    def browse_directory(self):
        """Abre diálogo para selecionar diretório"""
        directory = filedialog.askdirectory(initialdir=self.obsidian_path)
        if directory:
            self.dir_var.set(directory)
            self.obsidian_path = directory
    
    def save_api_key(self):
        """Salva a chave da API"""
        self.save_config()
        messagebox.showinfo("Sucesso", "Chave da API salva com sucesso!")
    
    def test_api_connection(self):
        """Testa a conexão com a API"""
        if not self.api_key.get():
            messagebox.showwarning("Aviso", "Por favor, insira a chave da API primeiro!")
            return
        
        def test_connection():
            try:
                self.root.after(0, self.update_status, "Testando conexão com API...")
                self.root.after(0, self.progress.start)
                
                response = self.call_gemini_api("Olá, você está funcionando?", "")
                
                self.root.after(0, messagebox.showinfo, "Sucesso", "✅ Conexão com API funcionando corretamente!")
                self.root.after(0, self.update_status, "API testada com sucesso")
                
            except Exception as e:
                error_msg = f"❌ Erro na conexão: {str(e)}"
                self.root.after(0, messagebox.showerror, "Erro", error_msg)
                self.root.after(0, self.update_status, "Erro na conexão com API")
            finally:
                self.root.after(0, self.progress.stop)
        
        threading.Thread(target=test_connection, daemon=True).start()
    
    def update_status(self, message):
        """Atualiza a mensagem de status"""
        self.status_var.set(message)
    
    def save_config(self):
        """Salva configurações no arquivo"""
        config = {
            'api_key': self.api_key.get(),
            'obsidian_path': self.obsidian_path
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar configurações: {e}")
    
    def load_config(self):
        """Carrega configurações do arquivo"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.api_key.set(config.get('api_key', ''))
                    self.obsidian_path = config.get('obsidian_path', self.obsidian_path)
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
    
    def run(self):
        """Inicia a aplicação"""
        # Mensagem de boas-vindas
        welcome_msg = """🎉 Bem-vindo ao Obsidian AI Manager!

Este sistema permite que você converse com suas anotações do Obsidian usando IA.

## Para começar:
1. **Configure** sua chave da API do Gemini na aba 'Configurações'
2. **Escaneie** suas notas clicando em 'Escanear Notas'
3. **Volte** para esta aba e comece a fazer perguntas!

### 💡 Exemplos de perguntas:
- *"Quais anotações falam sobre Python?"*
- *"Onde está a informação sobre reunião do projeto X?"*
- *"Resuma o conteúdo das minhas notas sobre machine learning"*

> **Dica:** A IA agora suporta formatação Markdown nas respostas!
> Use `código` entre crases, **negrito** e *itálico* normalmente.
"""
        
        self.add_to_chat("Sistema", welcome_msg, "system")
        
        # Focar no campo de entrada
        self.message_entry.focus_set()
        
        # Iniciar loop principal
        self.root.mainloop()

if __name__ == "__main__":
    app = ObsidianAIManager()
    app.run()
