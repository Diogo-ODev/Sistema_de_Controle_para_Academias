"""
SISTEMA DE GESTAO DE ACADEMIA - COM TELAS E LOGIN (TKINTER)
Versao 4

Novidades:
- EDICAO de alunos e funcionarios (Listar -> selecionar -> Editar, ou duplo clique).
- CPF UNICO entre Dono, Funcionarios e Alunos: o sistema compara so os numeros
  (com ou sem pontos/traco) nas 3 tabelas antes de cadastrar ou editar.
- O Dono agora tem CPF (campo novo no cadastro da academia e opcao
  "Editar Dados do Dono / Academia" para bancos antigos).
- Botoes sempre visiveis (rodape fixo) e formularios com rolagem.
"""

import re
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

NOME_BANCO = "academia.db"

DIAS_DA_SEMANA = [
    "Segunda-feira", "Terca-feira", "Quarta-feira",
    "Quinta-feira", "Sexta-feira", "Sabado", "Domingo"
]

# ==========================================================
# PALETA / TIPOGRAFIA
# ==========================================================

COR_FUNDO = "#eef2f7"
COR_FUNDO_CARD = "#ffffff"
COR_BARRA = "#1e3a8a"
COR_PRIMARIA = "#2563eb"
COR_PRIMARIA_ESCURA = "#1d4ed8"
COR_SECUNDARIA = "#0ea5e9"
COR_SUCESSO = "#16a34a"
COR_PERIGO = "#dc2626"
COR_AVISO = "#d97706"
COR_NEUTRO = "#64748b"
COR_TEXTO = "#0f172a"
COR_TEXTO_CLARO = "#f8fafc"
COR_BORDA = "#dbeafe"

FONTE_TITULO = ("Segoe UI", 19, "bold")
FONTE_SUBTITULO = ("Segoe UI", 11)
FONTE_SECAO = ("Segoe UI", 11, "bold")
FONTE_LABEL = ("Segoe UI", 10)
FONTE_LABEL_NEGRITO = ("Segoe UI", 10, "bold")
FONTE_BOTAO = ("Segoe UI", 10, "bold")

# Definicao dos formularios de pessoas (usado no cadastro E na edicao)
# tipos de campo: texto, cpf, senha, data, numero, decimal
DEFINICAO_PESSOAS = {
    "personal": {
        "tabela": "personais",
        "nome": "Funcionario",
        "campos": [
            ("nome", "Nome completo:", "texto"),
            ("cpf", "CPF (sera o login dele):", "cpf"),
            ("senha", "Senha de acesso:", "senha"),
            ("data_nascimento", "Data de nascimento (dd/mm/aaaa):", "data"),
            ("telefone", "Telefone:", "numero"),
            ("email", "Email:", "texto"),
            ("endereco", "Endereco:", "texto"),
            ("cref", "Numero do CREF:", "numero"),
            ("especialidade", "Especialidade:", "texto"),
        ],
    },
    "aluno": {
        "tabela": "alunos",
        "nome": "Aluno",
        "campos": [
            ("nome", "Nome completo:", "texto"),
            ("cpf", "CPF (sera o login dele):", "cpf"),
            ("senha", "Senha de acesso:", "senha"),
            ("data_nascimento", "Data de nascimento (dd/mm/aaaa):", "data"),
            ("telefone", "Telefone:", "numero"),
            ("email", "Email:", "texto"),
            ("endereco", "Endereco:", "texto"),
            ("objetivo", "Objetivo (ex: emagrecimento, hipertrofia):", "texto"),
            ("plano", "Plano (ex: mensal, trimestral, anual):", "texto"),
            ("valor_mensalidade", "Valor da mensalidade (ex: 150.00):", "decimal"),
        ],
    },
}


# ==========================================================
# BANCO DE DADOS
# ==========================================================

def conectar():
    conexao = sqlite3.connect(NOME_BANCO)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj TEXT,
            telefone TEXT,
            email TEXT NOT NULL UNIQUE,
            endereco TEXT,
            senha TEXT NOT NULL,
            data_cadastro TEXT,
            cpf TEXT
        )
    """)

    # migracao: bancos antigos nao tinham a coluna cpf na tabela academia
    cursor.execute("PRAGMA table_info(academia)")
    colunas_academia = [linha[1] for linha in cursor.fetchall()]
    if "cpf" not in colunas_academia:
        cursor.execute("ALTER TABLE academia ADD COLUMN cpf TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE,
            senha TEXT,
            data_nascimento TEXT,
            telefone TEXT,
            email TEXT,
            endereco TEXT,
            cref TEXT,
            especialidade TEXT,
            data_cadastro TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE,
            senha TEXT,
            data_nascimento TEXT,
            telefone TEXT,
            email TEXT,
            endereco TEXT,
            objetivo TEXT,
            plano TEXT,
            valor_mensalidade REAL,
            personal_id INTEGER,
            data_cadastro TEXT,
            FOREIGN KEY (personal_id) REFERENCES personais(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS treinos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER NOT NULL,
            personal_id INTEGER NOT NULL,
            tipo_treino TEXT,
            descricao TEXT,
            dia_semana TEXT,
            data_criacao TEXT,
            FOREIGN KEY (aluno_id) REFERENCES alunos(id),
            FOREIGN KEY (personal_id) REFERENCES personais(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER NOT NULL,
            personal_id INTEGER NOT NULL,
            data_aula TEXT,
            horario TEXT,
            status TEXT DEFAULT 'AGENDADA',
            FOREIGN KEY (aluno_id) REFERENCES alunos(id),
            FOREIGN KEY (personal_id) REFERENCES personais(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER NOT NULL,
            valor REAL,
            mes_referencia TEXT,
            data_vencimento TEXT,
            data_pagamento TEXT,
            status TEXT DEFAULT 'PENDENTE',
            FOREIGN KEY (aluno_id) REFERENCES alunos(id)
        )
    """)

    conexao.commit()
    conexao.close()


def academia_existe():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT COUNT(*) FROM academia")
    total = cursor.fetchone()[0]
    conexao.close()
    return total > 0


def data_hoje():
    return datetime.now().strftime("%d/%m/%Y")


# ==========================================================
# CPF: normalizacao e verificacao de duplicidade
# ==========================================================

def so_digitos(texto):
    return re.sub(r"\D", "", texto or "")


def mascarar_cpf(texto):
    cpf = so_digitos(texto)[:11]
    if len(cpf) > 9:
        return cpf[:3] + "." + cpf[3:6] + "." + cpf[6:9] + "-" + cpf[9:]
    if len(cpf) > 6:
        return cpf[:3] + "." + cpf[3:6] + "." + cpf[6:]
    if len(cpf) > 3:
        return cpf[:3] + "." + cpf[3:]
    return cpf


def cpf_em_uso(cpf, ignorar_tabela=None, ignorar_id=None):
    """Procura o CPF (comparando so os numeros) no Dono, Funcionarios e Alunos.
    Retorna (tipo, nome) de quem ja usa, ou None se estiver livre.
    ignorar_tabela/ignorar_id: registro que esta sendo editado (nao conta como duplicado)."""
    digitos = so_digitos(cpf)
    if not digitos:
        return None

    tabelas = (("academia", "Dono"), ("personais", "Funcionario"), ("alunos", "Aluno"))
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        for tabela, rotulo in tabelas:
            cursor.execute(
                f"SELECT id, nome FROM {tabela} "
                "WHERE REPLACE(REPLACE(REPLACE(cpf, '.', ''), '-', ''), ' ', '') = ?",
                (digitos,))
            for registro_id, nome in cursor.fetchall():
                if tabela == ignorar_tabela and registro_id == ignorar_id:
                    continue
                return rotulo, nome
    finally:
        conexao.close()
    return None


# ==========================================================
# VALIDACAO E FORMATACAO DE CAMPOS
# ==========================================================

def apenas_numeros(valor):
    return valor.isdigit() or valor == ""


def numero_decimal(valor):
    return valor == "" or re.fullmatch(r"\d*[.,]?\d*", valor) is not None


def formatar_cpf(event):
    texto = mascarar_cpf(event.widget.get())
    event.widget.delete(0, tk.END)
    event.widget.insert(0, texto)


def formatar_data(event):
    data = ''.join(filter(str.isdigit, event.widget.get()))[:8]
    if len(data) > 4:
        data = data[:2] + "/" + data[2:4] + "/" + data[4:]
    elif len(data) > 2:
        data = data[:2] + "/" + data[2:]
    event.widget.delete(0, tk.END)
    event.widget.insert(0, data)


def formatar_hora(event):
    hora = ''.join(filter(str.isdigit, event.widget.get()))[:4]
    if len(hora) > 2:
        hora = hora[:2] + ":" + hora[2:]
    event.widget.delete(0, tk.END)
    event.widget.insert(0, hora)


def preencher(entrada, valor):
    """Escreve um valor num Entry mesmo que ele tenha validacao de teclado."""
    entrada.config(validate="none")
    entrada.delete(0, tk.END)
    entrada.insert(0, "" if valor is None else str(valor))
    entrada.config(validate="key")


# ==========================================================
# APLICACAO PRINCIPAL
# ==========================================================

class AcademiaApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestao de Academia")
        self.configure(bg=COR_FUNDO)

        largura = min(620, self.winfo_screenwidth() - 40)
        altura = min(780, self.winfo_screenheight() - 100)
        x = (self.winfo_screenwidth() - largura) // 2
        y = max((self.winfo_screenheight() - altura) // 2 - 20, 0)
        self.geometry(f"{largura}x{altura}+{x}+{y}")
        self.minsize(460, 460)

        # estado da sessao
        self.usuario_logado_tipo = None
        self.usuario_logado_id = None
        self.usuario_logado_nome = None

        self.vcmd_numeros = (self.register(apenas_numeros), "%P")
        self.vcmd_decimal = (self.register(numero_decimal), "%P")

        self._configurar_estilo_ttk()

        self.barra_topo = tk.Frame(self, bg=COR_BARRA, height=54)
        self.barra_topo.pack(fill="x", side="top")
        self.barra_topo.pack_propagate(False)

        tk.Label(self.barra_topo, text="ACADEMIA FIT", bg=COR_BARRA, fg=COR_TEXTO_CLARO,
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=16)

        self.lbl_sessao = tk.Label(self.barra_topo, text="", bg=COR_BARRA,
                                   fg="#bfdbfe", font=("Segoe UI", 9))
        self.lbl_sessao.pack(side="right", padx=16)

        self.container = tk.Frame(self, bg=COR_FUNDO)
        self.container.pack(fill="both", expand=True)

        criar_tabelas()

        if academia_existe():
            self.verificar_cobranca_automatica()
            self.tela_login()
        else:
            self.tela_cadastro_academia()

    # ------------------------------------------------------
    # ESTILO
    # ------------------------------------------------------
    def _configurar_estilo_ttk(self):
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass

        estilo.configure("Treeview", rowheight=28, font=("Segoe UI", 10),
                         background=COR_FUNDO_CARD, fieldbackground=COR_FUNDO_CARD,
                         foreground=COR_TEXTO, borderwidth=0)
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                         background="#dbeafe", foreground=COR_TEXTO, relief="flat")
        estilo.map("Treeview", background=[("selected", COR_PRIMARIA)],
                   foreground=[("selected", "white")])
        estilo.configure("TCombobox", font=("Segoe UI", 10))

    # ------------------------------------------------------
    # HELPERS DE INTERFACE
    # ------------------------------------------------------
    def limpar_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def atualizar_barra_sessao(self):
        if self.usuario_logado_nome:
            rotulos = {"dono": "Dono", "funcionario": "Funcionario", "aluno": "Aluno"}
            texto = f"{self.usuario_logado_nome}  ·  {rotulos.get(self.usuario_logado_tipo, '')}"
        else:
            texto = ""
        self.lbl_sessao.config(text=texto)

    def _rolavel(self, parent, bg=COR_FUNDO):
        """Cria uma area com barra de rolagem. Retorna o frame interno."""
        canvas = tk.Canvas(parent, bg=bg, highlightthickness=0)
        barra = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        interno = tk.Frame(canvas, bg=bg)
        janela_id = canvas.create_window((0, 0), window=interno, anchor="nw")

        interno.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(janela_id, width=e.width))
        canvas.configure(yscrollcommand=barra.set)

        barra.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def rolar(event):
            try:
                w = canvas.winfo_containing(event.x_root, event.y_root)
                dentro = False
                while w is not None:
                    if w == canvas:
                        dentro = True
                        break
                    w = w.master
                if not dentro:
                    return
                if interno.winfo_reqheight() <= canvas.winfo_height():
                    return
                if event.num == 4:
                    d = -1
                elif event.num == 5:
                    d = 1
                else:
                    d = -1 if event.delta > 0 else 1
                canvas.yview_scroll(d, "units")
            except (tk.TclError, KeyError):
                pass

        canvas.bind_all("<MouseWheel>", rolar, add="+")
        canvas.bind_all("<Button-4>", rolar, add="+")
        canvas.bind_all("<Button-5>", rolar, add="+")
        return interno

    def nova_tela(self):
        """Limpa a tela principal. Retorna (corpo_rolavel, rodape_fixo)."""
        self.limpar_container()
        rodape = tk.Frame(self.container, bg=COR_FUNDO)
        rodape.pack(side="bottom", fill="x")
        corpo = self._rolavel(self.container, COR_FUNDO)
        return corpo, rodape

    def cabecalho(self, parent, titulo, subtitulo=None):
        bloco = tk.Frame(parent, bg=COR_FUNDO)
        bloco.pack(fill="x", padx=24, pady=(22, 10))
        tk.Label(bloco, text=titulo, font=FONTE_TITULO, bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor="w")
        if subtitulo:
            tk.Label(bloco, text=subtitulo, font=FONTE_SUBTITULO, bg=COR_FUNDO,
                     fg=COR_NEUTRO).pack(anchor="w", pady=(2, 0))
        return bloco

    def rotulo_secao(self, parent, texto):
        tk.Label(parent, text=texto.upper(), font=FONTE_SECAO, bg=COR_FUNDO,
                 fg=COR_PRIMARIA_ESCURA).pack(anchor="w", padx=24, pady=(16, 4))

    def campo_form(self, parent, rotulo, largura=34, **kw):
        """Rotulo + Entry dentro de um card branco."""
        tk.Label(parent, text=rotulo, font=FONTE_LABEL, bg=COR_FUNDO_CARD,
                 fg=COR_TEXTO).pack(anchor="w", pady=(8, 2))
        entrada = tk.Entry(parent, width=largura, font=FONTE_LABEL, relief="solid", bd=1,
                           highlightthickness=1, highlightbackground=COR_BORDA,
                           highlightcolor=COR_PRIMARIA, **kw)
        entrada.pack(anchor="w", ipady=4)
        return entrada

    def botao(self, parent, texto, comando, cor=COR_PRIMARIA, cor_texto="white", largura=None):
        b = tk.Button(parent, text=texto, command=comando, bg=cor, fg=cor_texto,
                      activebackground=cor, activeforeground=cor_texto,
                      font=FONTE_BOTAO, relief="flat", bd=0, cursor="hand2",
                      padx=14, pady=9)
        if largura:
            b.config(width=largura)
        return b

    def botao_menu(self, parent, texto, comando):
        b = tk.Button(parent, text=texto, command=comando, bg=COR_FUNDO_CARD, fg=COR_TEXTO,
                      activebackground=COR_BORDA, font=FONTE_LABEL_NEGRITO, relief="flat",
                      bd=0, cursor="hand2", anchor="w", padx=16, pady=11,
                      highlightthickness=1, highlightbackground=COR_BORDA)
        b.pack(fill="x", padx=24, pady=3)
        return b

    def criar_janela(self, titulo, largura, altura):
        """Janela ajustada a tela, centralizada e redimensionavel."""
        janela = tk.Toplevel(self)
        janela.title(titulo)
        largura = min(largura, self.winfo_screenwidth() - 60)
        altura = min(altura, self.winfo_screenheight() - 100)
        x = (self.winfo_screenwidth() - largura) // 2
        y = max((self.winfo_screenheight() - altura) // 2 - 20, 0)
        janela.geometry(f"{largura}x{altura}+{x}+{y}")
        janela.minsize(min(360, largura), min(300, altura))
        janela.configure(bg=COR_FUNDO)
        janela.transient(self)
        return janela

    def criar_janela_rodape(self, titulo, largura, altura):
        """Janela com rodape fixo (para botoes). Retorna (janela, rodape)."""
        janela = self.criar_janela(titulo, largura, altura)
        rodape = tk.Frame(janela, bg=COR_FUNDO)
        rodape.pack(side="bottom", fill="x", padx=16, pady=12)
        return janela, rodape

    def criar_janela_form(self, titulo, largura, altura, titulo_interno=None):
        """Janela de formulario: rodape fixo + corpo rolavel + card branco.
        Retorna (janela, card, rodape)."""
        janela, rodape = self.criar_janela_rodape(titulo, largura, altura)
        area = tk.Frame(janela, bg=COR_FUNDO)
        area.pack(fill="both", expand=True)
        corpo = self._rolavel(area, COR_FUNDO)

        tk.Label(corpo, text=titulo_interno or titulo, font=FONTE_SECAO, bg=COR_FUNDO,
                 fg=COR_PRIMARIA_ESCURA).pack(pady=(14, 6))

        moldura = tk.Frame(corpo, bg=COR_FUNDO_CARD, highlightthickness=1,
                           highlightbackground=COR_BORDA)
        moldura.pack(fill="x", padx=16, pady=6)
        card = tk.Frame(moldura, bg=COR_FUNDO_CARD)
        card.pack(fill="x", padx=16, pady=12)
        return janela, card, rodape

    def criar_tabela(self, parent, colunas, altura=8):
        moldura = tk.Frame(parent, bg=COR_FUNDO)
        moldura.pack(fill="both", expand=True, padx=24, pady=6)

        tabela = ttk.Treeview(moldura, columns=colunas, show="headings", height=altura)
        for coluna in colunas:
            tabela.heading(coluna, text=coluna)
            tabela.column(coluna, width=120, anchor="w")

        barra = ttk.Scrollbar(moldura, orient="vertical", command=tabela.yview)
        tabela.configure(yscrollcommand=barra.set)
        tabela.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        return tabela

    def janela_lista(self, titulo, largura, altura, colunas, linhas, msg_vazio):
        """Janela padrao de listagem. linhas = [(iid, (valores...)), ...]"""
        janela, rodape = self.criar_janela_rodape(titulo, largura, altura)
        self.botao(rodape, "Fechar", janela.destroy, cor=COR_NEUTRO).pack(side="right")

        tk.Label(janela, text=titulo, font=FONTE_SECAO, bg=COR_FUNDO,
                 fg=COR_PRIMARIA_ESCURA).pack(pady=(16, 6))
        if not linhas:
            tk.Label(janela, text=msg_vazio, bg=COR_FUNDO, fg=COR_NEUTRO,
                     font=FONTE_LABEL).pack(pady=4)

        tabela = self.criar_tabela(janela, colunas, altura=12)
        for iid, valores in linhas:
            tabela.insert("", "end", iid=str(iid), values=valores)
        return janela, tabela

    # ==========================================================
    # TELA 1 - CADASTRO DA ACADEMIA
    # ==========================================================
    def tela_cadastro_academia(self):
        corpo, rodape = self.nova_tela()
        self.atualizar_barra_sessao()

        self.cabecalho(corpo, "Bem-vindo!", "Vamos cadastrar a sua academia")

        moldura = tk.Frame(corpo, bg=COR_FUNDO_CARD, highlightthickness=1,
                           highlightbackground=COR_BORDA)
        moldura.pack(fill="x", padx=24, pady=10)
        card = tk.Frame(moldura, bg=COR_FUNDO_CARD)
        card.pack(fill="x", padx=20, pady=16)

        entry_nome = self.campo_form(card, "Nome da academia:")
        entry_cnpj = self.campo_form(card, "CNPJ:")
        entry_cpf = self.campo_form(card, "CPF do dono:")
        entry_cpf.bind("<KeyRelease>", formatar_cpf)
        entry_telefone = self.campo_form(card, "Telefone:", validate="key",
                                         validatecommand=self.vcmd_numeros)
        entry_endereco = self.campo_form(card, "Endereco:")
        entry_email = self.campo_form(card, "Email do dono (sera o login):")
        entry_senha = self.campo_form(card, "Senha do dono:", show="*")

        def salvar_academia():
            nome = entry_nome.get().strip()
            email = entry_email.get().strip()
            senha = entry_senha.get()
            cpf = entry_cpf.get().strip()

            if nome == "" or email == "" or senha == "" or cpf == "":
                messagebox.showerror("Erro", "Nome, CPF, email e senha sao obrigatorios.")
                return
            if len(so_digitos(cpf)) != 11:
                messagebox.showerror("Erro", "CPF invalido. Informe os 11 numeros.")
                return

            conexao = conectar()
            cursor = conexao.cursor()
            try:
                cursor.execute("""
                    INSERT INTO academia (nome, cnpj, cpf, telefone, email, endereco, senha, data_cadastro)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (nome, entry_cnpj.get(), mascarar_cpf(cpf), entry_telefone.get(), email,
                      entry_endereco.get(), senha, data_hoje()))
                conexao.commit()
                messagebox.showinfo("Sucesso", "Academia cadastrada com sucesso!\nAgora faca login como Dono.")
                self.tela_login()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Ja existe uma academia cadastrada com esse email.")
            finally:
                conexao.close()

        self.botao(rodape, "Cadastrar Academia", salvar_academia,
                   cor=COR_SUCESSO).pack(padx=24, pady=12, anchor="w")

    # ==========================================================
    # TELA 2 - LOGIN
    # ==========================================================
    def tela_login(self):
        self.usuario_logado_tipo = None
        self.usuario_logado_id = None
        self.usuario_logado_nome = None
        corpo, rodape = self.nova_tela()
        self.atualizar_barra_sessao()

        self.cabecalho(corpo, "Academia Fit", "Escolha o tipo de acesso")

        opcoes = [
            ("Sou o Dono da Academia", "dono"),
            ("Sou Funcionario (Personal)", "funcionario"),
            ("Sou Aluno", "aluno"),
        ]
        for texto, tipo in opcoes:
            b = self.botao(corpo, texto, lambda t=tipo: self.tela_formulario_login(t),
                           cor=COR_FUNDO_CARD, cor_texto=COR_TEXTO)
            b.config(anchor="w", highlightthickness=1, highlightbackground=COR_BORDA, justify="left")
            b.pack(fill="x", padx=24, pady=8, ipady=6)

    def tela_formulario_login(self, tipo):
        corpo, rodape = self.nova_tela()

        titulos = {
            "dono": "Login - Dono da Academia",
            "funcionario": "Login - Funcionario",
            "aluno": "Login - Aluno",
        }
        self.cabecalho(corpo, titulos[tipo])

        moldura = tk.Frame(corpo, bg=COR_FUNDO_CARD, highlightthickness=1,
                           highlightbackground=COR_BORDA)
        moldura.pack(fill="x", padx=24, pady=10)
        interno = tk.Frame(moldura, bg=COR_FUNDO_CARD)
        interno.pack(fill="x", padx=20, pady=18)

        entry_login = self.campo_form(interno, "Email:" if tipo == "dono" else "CPF:", largura=30)
        if tipo != "dono":
            entry_login.bind("<KeyRelease>", formatar_cpf)
        entry_senha = self.campo_form(interno, "Senha:", largura=30, show="*")
        entry_login.focus_set()

        def entrar(_event=None):
            valor_login = entry_login.get().strip()
            senha = entry_senha.get()

            conexao = conectar()
            cursor = conexao.cursor()

            if tipo == "dono":
                cursor.execute("SELECT id, nome, senha FROM academia WHERE email = ?", (valor_login,))
            else:
                tabela = "personais" if tipo == "funcionario" else "alunos"
                # compara so os numeros, entao funciona com CPF antigo sem mascara tambem
                cursor.execute(
                    f"SELECT id, nome, senha FROM {tabela} "
                    "WHERE REPLACE(REPLACE(REPLACE(cpf, '.', ''), '-', ''), ' ', '') = ?",
                    (so_digitos(valor_login),))

            resultado = cursor.fetchone()
            conexao.close()

            if not resultado:
                messagebox.showerror("Erro", "Usuario nao encontrado.")
                return

            id_encontrado, nome_encontrado, senha_encontrada = resultado
            if senha != senha_encontrada:
                messagebox.showerror("Erro", "Senha incorreta.")
                return

            self.usuario_logado_tipo = tipo
            self.usuario_logado_id = id_encontrado
            self.usuario_logado_nome = nome_encontrado
            self.atualizar_barra_sessao()

            if tipo == "dono":
                self.tela_dono()
            elif tipo == "funcionario":
                self.tela_funcionario()
            else:
                self.tela_aluno()

        entry_senha.bind("<Return>", entrar)
        entry_login.bind("<Return>", entrar)

        botoes = tk.Frame(rodape, bg=COR_FUNDO)
        botoes.pack(padx=24, pady=12, anchor="w")
        self.botao(botoes, "Entrar", entrar, cor=COR_SUCESSO).pack(side="left", padx=(0, 8))
        self.botao(botoes, "Voltar", self.tela_login, cor=COR_PERIGO).pack(side="left")

    # ==========================================================
    # TELA DO DONO
    # ==========================================================
    def tela_dono(self):
        corpo, rodape = self.nova_tela()
        self.cabecalho(corpo, f"Ola, {self.usuario_logado_nome}", "Acesso: Dono da academia")

        self.rotulo_secao(corpo, "Cadastros")
        self.botao_menu(corpo, "Cadastrar Funcionario", lambda: self.formulario_pessoa("personal"))
        self.botao_menu(corpo, "Listar / Editar Funcionarios", self.abrir_lista_personais)
        self.botao_menu(corpo, "Cadastrar Aluno", lambda: self.formulario_pessoa("aluno"))
        self.botao_menu(corpo, "Listar / Editar Alunos", self.abrir_lista_alunos)
        self.botao_menu(corpo, "Atribuir Aluno a um Funcionario", self.abrir_atribuir_personal)

        self.rotulo_secao(corpo, "Treinos e Agenda")
        self.botao_menu(corpo, "Gerenciar Treinos (criar / editar / excluir)",
                        lambda: self.abrir_gerenciar_treinos(None))
        self.botao_menu(corpo, "Agendar Aula", lambda: self.abrir_agendar_aula(None))
        self.botao_menu(corpo, "Ver Agendamentos", lambda: self.abrir_ver_agendamentos(None))

        self.rotulo_secao(corpo, "Financeiro")
        self.botao_menu(corpo, "Gerar Cobrancas do Mes", self.gerar_cobrancas_do_mes)
        self.botao_menu(corpo, "Ver Pagamentos", self.abrir_ver_pagamentos)
        self.botao_menu(corpo, "Marcar Pagamento como Pago", self.abrir_marcar_pagamento)

        self.rotulo_secao(corpo, "Minha Conta")
        self.botao_menu(corpo, "Editar Dados do Dono / Academia", self.formulario_academia)

        tk.Frame(corpo, bg=COR_FUNDO, height=12).pack()
        self.botao(rodape, "Sair (Logout)", self.tela_login, cor=COR_PERIGO).pack(padx=24, pady=12, anchor="w")

    # ==========================================================
    # EDITAR DADOS DO DONO / ACADEMIA
    # ==========================================================
    def formulario_academia(self):
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT nome, cnpj, cpf, telefone, email, endereco FROM academia WHERE id = ?",
                       (self.usuario_logado_id,))
        dados = cursor.fetchone()
        conexao.close()
        if not dados:
            messagebox.showerror("Erro", "Cadastro da academia nao encontrado.")
            return

        janela, f, rodape = self.criar_janela_form("Editar Dados do Dono / Academia", 420, 660)

        e_nome = self.campo_form(f, "Nome da academia:")
        e_cnpj = self.campo_form(f, "CNPJ:")
        e_cpf = self.campo_form(f, "CPF do dono:")
        e_cpf.bind("<KeyRelease>", formatar_cpf)
        e_tel = self.campo_form(f, "Telefone:", validate="key", validatecommand=self.vcmd_numeros)
        e_end = self.campo_form(f, "Endereco:")
        e_email = self.campo_form(f, "Email do dono (login):")
        e_senha = self.campo_form(f, "Nova senha (deixe em branco para manter):", show="*")

        for entrada, valor in zip((e_nome, e_cnpj, e_cpf, e_tel, e_email, e_end), dados):
            pass
        preencher(e_nome, dados[0])
        preencher(e_cnpj, dados[1])
        preencher(e_cpf, dados[2])
        preencher(e_tel, dados[3])
        preencher(e_email, dados[4])
        preencher(e_end, dados[5])

        def salvar():
            nome = e_nome.get().strip()
            email = e_email.get().strip()
            cpf = e_cpf.get().strip()
            senha = e_senha.get()

            if nome == "" or email == "" or cpf == "":
                messagebox.showerror("Erro", "Nome, CPF e email sao obrigatorios.", parent=janela)
                return
            if len(so_digitos(cpf)) != 11:
                messagebox.showerror("Erro", "CPF invalido. Informe os 11 numeros.", parent=janela)
                return

            em_uso = cpf_em_uso(cpf, "academia", self.usuario_logado_id)
            if em_uso:
                messagebox.showerror("CPF duplicado",
                                     f"Esse CPF ja esta cadastrado ({em_uso[0]}: {em_uso[1]}).",
                                     parent=janela)
                return

            conexao = conectar()
            cursor = conexao.cursor()
            try:
                cursor.execute("""
                    UPDATE academia SET nome = ?, cnpj = ?, cpf = ?, telefone = ?, email = ?, endereco = ?
                    WHERE id = ?
                """, (nome, e_cnpj.get(), mascarar_cpf(cpf), e_tel.get(), email, e_end.get(),
                      self.usuario_logado_id))
                if senha:
                    cursor.execute("UPDATE academia SET senha = ? WHERE id = ?",
                                   (senha, self.usuario_logado_id))
                conexao.commit()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Ja existe uma academia cadastrada com esse email.",
                                     parent=janela)
                return
            finally:
                conexao.close()

            self.usuario_logado_nome = nome
            self.atualizar_barra_sessao()
            messagebox.showinfo("Sucesso", "Dados atualizados com sucesso!", parent=janela)
            janela.destroy()
            self.tela_dono()

        self.botao(rodape, "Salvar", salvar, cor=COR_SUCESSO).pack(side="left", padx=(0, 8))
        self.botao(rodape, "Cancelar", janela.destroy, cor=COR_NEUTRO).pack(side="left")

    # ==========================================================
    # TELA DO FUNCIONARIO
    # ==========================================================
    def tela_funcionario(self):
        corpo, rodape = self.nova_tela()
        self.cabecalho(corpo, f"Ola, {self.usuario_logado_nome}", "Acesso: Funcionario / Personal")

        self.rotulo_secao(corpo, "Meus Alunos")
        self.botao_menu(corpo, "Ver Meus Alunos", self.abrir_meus_alunos)

        self.rotulo_secao(corpo, "Treinos e Agenda")
        self.botao_menu(corpo, "Gerenciar Treinos dos Meus Alunos",
                        lambda: self.abrir_gerenciar_treinos(self.usuario_logado_id))
        self.botao_menu(corpo, "Agendar Aula com um Aluno Meu",
                        lambda: self.abrir_agendar_aula(self.usuario_logado_id))
        self.botao_menu(corpo, "Ver Meus Agendamentos",
                        lambda: self.abrir_ver_agendamentos(self.usuario_logado_id))

        self.botao(rodape, "Sair (Logout)", self.tela_login, cor=COR_PERIGO).pack(padx=24, pady=12, anchor="w")

    def abrir_meus_alunos(self):
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, nome, cpf, plano FROM alunos WHERE personal_id = ?",
                       (self.usuario_logado_id,))
        resultado = cursor.fetchall()
        conexao.close()

        linhas = [(a[0], (a[1], a[2], a[3] or "-")) for a in resultado]
        self.janela_lista("Meus Alunos", 560, 440, ("Nome", "CPF", "Plano"), linhas,
                          "Voce ainda nao tem alunos atribuidos.")

    # ==========================================================
    # TELA DO ALUNO
    # ==========================================================
    def tela_aluno(self):
        corpo, rodape = self.nova_tela()
        self.cabecalho(corpo, f"Ola, {self.usuario_logado_nome}", "Acesso: Aluno")

        self.rotulo_secao(corpo, "Meu Painel")
        self.botao_menu(corpo, "Meus Treinos por Dia", self.abrir_meus_treinos_por_dia)
        self.botao_menu(corpo, "Meus Proximos Agendamentos", self.abrir_meus_agendamentos)

        self.botao(rodape, "Sair (Logout)", self.tela_login, cor=COR_PERIGO).pack(padx=24, pady=12, anchor="w")

    def abrir_meus_treinos_por_dia(self):
        janela, rodape = self.criar_janela_rodape("Meus Treinos por Dia", 620, 560)
        self.botao(rodape, "Fechar", janela.destroy, cor=COR_NEUTRO).pack(side="right")

        tk.Label(janela, text="Meus Treinos - por dia da semana", font=FONTE_SECAO,
                 bg=COR_FUNDO, fg=COR_PRIMARIA_ESCURA).pack(pady=(16, 6))

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT tipo_treino, descricao, dia_semana FROM treinos WHERE aluno_id = ?",
                       (self.usuario_logado_id,))
        treinos = cursor.fetchall()
        conexao.close()

        area = tk.Frame(janela, bg=COR_FUNDO)
        area.pack(fill="both", expand=True, padx=16)
        rolavel = self._rolavel(area, COR_FUNDO)

        if not treinos:
            tk.Label(rolavel, text="Voce ainda nao tem treinos cadastrados.", bg=COR_FUNDO,
                     fg=COR_NEUTRO, font=FONTE_LABEL).pack(pady=10)
            return

        for dia in DIAS_DA_SEMANA + [None]:
            treinos_do_dia = [t for t in treinos if t[2] == dia]
            if not treinos_do_dia:
                continue
            titulo_dia = dia if dia else "Sem dia definido"
            tk.Label(rolavel, text=titulo_dia.upper(), font=FONTE_LABEL_NEGRITO, bg=COR_FUNDO,
                     fg=COR_PRIMARIA_ESCURA).pack(anchor="w", pady=(14, 4))
            for t in treinos_do_dia:
                card = tk.Frame(rolavel, bg=COR_FUNDO_CARD, highlightthickness=1,
                                highlightbackground=COR_BORDA)
                card.pack(fill="x", pady=3)
                tk.Label(card, text=t[0] or "(sem tipo)", font=FONTE_LABEL_NEGRITO,
                         bg=COR_FUNDO_CARD, fg=COR_TEXTO).pack(anchor="w", padx=12, pady=(8, 0))
                tk.Label(card, text=t[1] or "", font=FONTE_LABEL, bg=COR_FUNDO_CARD,
                         fg=COR_NEUTRO, wraplength=500, justify="left").pack(anchor="w", padx=12, pady=(0, 8))

    def abrir_meus_agendamentos(self):
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT agendamentos.id, agendamentos.data_aula, agendamentos.horario,
                   personais.nome, agendamentos.status
            FROM agendamentos
            JOIN personais ON agendamentos.personal_id = personais.id
            WHERE agendamentos.aluno_id = ?
            ORDER BY agendamentos.data_aula, agendamentos.horario
        """, (self.usuario_logado_id,))
        resultado = cursor.fetchall()
        conexao.close()

        linhas = [(ag[0], (ag[1], ag[2], ag[3], ag[4])) for ag in resultado]
        self.janela_lista("Meus Proximos Agendamentos", 600, 460,
                          ("Data", "Horario", "Personal", "Status"), linhas,
                          "Voce nao tem nenhuma aula agendada.")

    # ==========================================================
    # FORMULARIO UNICO: CADASTRAR / EDITAR (funcionario e aluno)
    # registro_id = None -> cadastrar; registro_id = id -> editar
    # ao_salvar = funcao chamada depois de salvar (ex: recarregar a lista)
    # ==========================================================
    def formulario_pessoa(self, tipo, registro_id=None, ao_salvar=None):
        definicao = DEFINICAO_PESSOAS[tipo]
        tabela = definicao["tabela"]
        rotulo_tipo = definicao["nome"]
        campos = definicao["campos"]
        editando = registro_id is not None

        dados = {}
        if editando:
            colunas_dados = [c for c, _, _ in campos if c != "senha"]
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute(f"SELECT {', '.join(colunas_dados)} FROM {tabela} WHERE id = ?", (registro_id,))
            linha = cursor.fetchone()
            conexao.close()
            if not linha:
                messagebox.showerror("Erro", f"{rotulo_tipo} nao encontrado.")
                return
            dados = dict(zip(colunas_dados, linha))

        titulo = f"Editar {rotulo_tipo}" if editando else f"Cadastrar {rotulo_tipo}"
        altura = 660 if tipo == "personal" else 720
        janela, f, rodape = self.criar_janela_form(titulo, 430, altura, titulo)

        entradas = {}
        for coluna, rotulo, kind in campos:
            kw = {}
            if kind == "senha":
                kw["show"] = "*"
                if editando:
                    rotulo = "Nova senha (deixe em branco para manter):"
            elif kind == "numero":
                kw.update(validate="key", validatecommand=self.vcmd_numeros)
            elif kind == "decimal":
                kw.update(validate="key", validatecommand=self.vcmd_decimal)

            entrada = self.campo_form(f, rotulo, **kw)
            if kind == "cpf":
                entrada.bind("<KeyRelease>", formatar_cpf)
            elif kind == "data":
                entrada.bind("<KeyRelease>", formatar_data)

            if editando and coluna in dados:
                valor = dados[coluna]
                if kind == "decimal":
                    valor = f"{(valor or 0):.2f}"
                preencher(entrada, valor)
            entradas[coluna] = entrada

        def salvar():
            valores = {}
            for coluna, _, kind in campos:
                texto = entradas[coluna].get()
                valores[coluna] = texto if kind == "senha" else texto.strip()

            if valores["nome"] == "" or valores["cpf"] == "":
                messagebox.showerror("Erro", "Nome e CPF sao obrigatorios.", parent=janela)
                return
            if not editando and valores["senha"] == "":
                messagebox.showerror("Erro", "A senha e obrigatoria no cadastro.", parent=janela)
                return
            if len(so_digitos(valores["cpf"])) != 11:
                messagebox.showerror("Erro", "CPF invalido. Informe os 11 numeros.", parent=janela)
                return

            # ---- verificacao de CPF duplicado (Dono, Funcionarios e Alunos) ----
            em_uso = cpf_em_uso(valores["cpf"], tabela if editando else None, registro_id)
            if em_uso:
                messagebox.showerror(
                    "CPF duplicado",
                    f"Esse CPF ja esta cadastrado no sistema.\n\n{em_uso[0]}: {em_uso[1]}",
                    parent=janela)
                return
            valores["cpf"] = mascarar_cpf(valores["cpf"])

            if "valor_mensalidade" in valores:
                try:
                    valores["valor_mensalidade"] = float(valores["valor_mensalidade"].replace(",", "."))
                except ValueError:
                    valores["valor_mensalidade"] = 0.0
                    messagebox.showwarning("Aviso", "Valor invalido ou vazio, foi definido como 0.00. "
                                           "Voce pode corrigir depois.", parent=janela)

            conexao = conectar()
            cursor = conexao.cursor()
            try:
                if editando:
                    # senha em branco = mantem a atual
                    cols = [c for c in valores if c != "senha" or valores["senha"] != ""]
                    sets = ", ".join(f"{c} = ?" for c in cols)
                    cursor.execute(f"UPDATE {tabela} SET {sets} WHERE id = ?",
                                   [valores[c] for c in cols] + [registro_id])
                    mensagem = f"{rotulo_tipo} atualizado com sucesso!"
                else:
                    cols = list(valores.keys()) + ["data_cadastro"]
                    marcadores = ", ".join("?" for _ in cols)
                    cursor.execute(f"INSERT INTO {tabela} ({', '.join(cols)}) VALUES ({marcadores})",
                                   [valores[c] for c in valores] + [data_hoje()])
                    mensagem = f"{rotulo_tipo} cadastrado com sucesso! ID: {cursor.lastrowid}"
                conexao.commit()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Ja existe um cadastro com esse CPF.", parent=janela)
                return
            finally:
                conexao.close()

            messagebox.showinfo("Sucesso", mensagem, parent=janela)
            janela.destroy()
            if ao_salvar:
                ao_salvar()

        self.botao(rodape, "Salvar", salvar, cor=COR_SUCESSO).pack(side="left", padx=(0, 8))
        self.botao(rodape, "Cancelar", janela.destroy, cor=COR_NEUTRO).pack(side="left")

    # ==========================================================
    # LISTAS COM EDICAO (funcionarios e alunos)
    # ==========================================================
    def _lista_pessoas_editavel(self, tipo):
        definicao = DEFINICAO_PESSOAS[tipo]
        if tipo == "personal":
            titulo, largura = "Lista de Funcionarios", 660
            colunas = ("Nome", "CPF", "Telefone", "Especialidade")
            msg_vazio = "Nenhum funcionario cadastrado."
        else:
            titulo, largura = "Lista de Alunos", 700
            colunas = ("Nome", "CPF", "Plano", "Personal")
            msg_vazio = "Nenhum aluno cadastrado."

        janela, rodape = self.criar_janela_rodape(titulo, largura, 500)

        tk.Label(janela, text=titulo, font=FONTE_SECAO, bg=COR_FUNDO,
                 fg=COR_PRIMARIA_ESCURA).pack(pady=(16, 2))
        tk.Label(janela, text="Selecione uma linha e clique em Editar (ou de duplo clique).",
                 font=("Segoe UI", 9), bg=COR_FUNDO, fg=COR_NEUTRO).pack()
        lbl_vazio = tk.Label(janela, text="", bg=COR_FUNDO, fg=COR_NEUTRO, font=FONTE_LABEL)
        lbl_vazio.pack()

        tabela = self.criar_tabela(janela, colunas, altura=12)

        def carregar():
            for item in tabela.get_children():
                tabela.delete(item)
            conexao = conectar()
            cursor = conexao.cursor()
            if tipo == "personal":
                cursor.execute("SELECT id, nome, cpf, telefone, especialidade FROM personais ORDER BY nome")
                linhas = [(p[0], (p[1], p[2], p[3] or "-", p[4] or "-")) for p in cursor.fetchall()]
            else:
                cursor.execute("""
                    SELECT alunos.id, alunos.nome, alunos.cpf, alunos.plano, personais.nome
                    FROM alunos
                    LEFT JOIN personais ON alunos.personal_id = personais.id
                    ORDER BY alunos.nome
                """)
                linhas = [(a[0], (a[1], a[2], a[3] or "-", a[4] if a[4] else "Sem personal"))
                          for a in cursor.fetchall()]
            conexao.close()
            for iid, valores in linhas:
                tabela.insert("", "end", iid=str(iid), values=valores)
            lbl_vazio.config(text="" if linhas else msg_vazio)

        def editar(_event=None):
            selecao = tabela.selection()
            if not selecao:
                messagebox.showerror("Erro", "Selecione uma linha na tabela para editar.", parent=janela)
                return
            self.formulario_pessoa(tipo, int(selecao[0]), ao_salvar=carregar)

        def novo():
            self.formulario_pessoa(tipo, None, ao_salvar=carregar)

        tabela.bind("<Double-1>", editar)

        self.botao(rodape, "Novo", novo, cor=COR_SUCESSO).pack(side="left", padx=(0, 6))
        self.botao(rodape, "Editar", editar, cor=COR_SECUNDARIA).pack(side="left", padx=(0, 6))
        self.botao(rodape, "Fechar", janela.destroy, cor=COR_NEUTRO).pack(side="right")

        carregar()

    def abrir_lista_personais(self):
        self._lista_pessoas_editavel("personal")

    def abrir_lista_alunos(self):
        self._lista_pessoas_editavel("aluno")

    # ==========================================================
    # ATRIBUIR ALUNO A UM FUNCIONARIO
    # ==========================================================
    def abrir_atribuir_personal(self):
        janela, rodape = self.criar_janela_rodape("Atribuir Aluno a um Funcionario", 500, 640)

        tk.Label(janela, text="Atribuir Aluno a um Funcionario", font=FONTE_SECAO, bg=COR_FUNDO,
                 fg=COR_PRIMARIA_ESCURA).pack(pady=(16, 6))

        tk.Label(janela, text="Selecione o aluno:", font=FONTE_LABEL,
                 bg=COR_FUNDO).pack(anchor="w", padx=24)
        tabela_alunos = self.criar_tabela(janela, ("Nome", "CPF"), altura=6)

        tk.Label(janela, text="Selecione o funcionario:", font=FONTE_LABEL,
                 bg=COR_FUNDO).pack(anchor="w", padx=24, pady=(10, 0))
        tabela_personais = self.criar_tabela(janela, ("Nome", "CPF"), altura=6)

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, nome, cpf FROM alunos")
        for a in cursor.fetchall():
            tabela_alunos.insert("", "end", iid=str(a[0]), values=(a[1], a[2]))
        cursor.execute("SELECT id, nome, cpf FROM personais")
        for p in cursor.fetchall():
            tabela_personais.insert("", "end", iid=str(p[0]), values=(p[1], p[2]))
        conexao.close()

        def salvar_atribuicao():
            selecao_aluno = tabela_alunos.selection()
            selecao_personal = tabela_personais.selection()

            if not selecao_aluno:
                messagebox.showerror("Erro", "Selecione um aluno na tabela.", parent=janela)
                return
            if not selecao_personal:
                messagebox.showerror("Erro", "Selecione um funcionario na tabela.", parent=janela)
                return

            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute("UPDATE alunos SET personal_id = ? WHERE id = ?",
                           (selecao_personal[0], selecao_aluno[0]))
            conexao.commit()
            conexao.close()

            messagebox.showinfo("Sucesso", "Aluno atribuido ao funcionario com sucesso!", parent=janela)
            janela.destroy()

        self.botao(rodape, "Atribuir", salvar_atribuicao, cor=COR_SUCESSO).pack(side="left", padx=(0, 8))
        self.botao(rodape, "Cancelar", janela.destroy, cor=COR_NEUTRO).pack(side="left")

    # ==========================================================
    # CRUD DE TREINOS
    # ==========================================================
    def abrir_gerenciar_treinos(self, personal_id_fixo):
        janela, rodape = self.criar_janela_rodape("Gerenciar Treinos", 780, 680)

        tk.Label(janela, text="Gerenciar Treinos", font=FONTE_SECAO, bg=COR_FUNDO,
                 fg=COR_PRIMARIA_ESCURA).pack(pady=(14, 4))

        estado = {"aluno_id": None}

        tk.Label(janela, text="1. Selecione o aluno", font=FONTE_LABEL_NEGRITO, bg=COR_FUNDO,
                 fg=COR_TEXTO).pack(anchor="w", padx=24, pady=(6, 0))
        tabela_alunos = self.criar_tabela(janela, ("Nome", "CPF", "Plano"), altura=5)

        conexao = conectar()
        cursor = conexao.cursor()
        if personal_id_fixo:
            cursor.execute("SELECT id, nome, cpf, plano FROM alunos WHERE personal_id = ?", (personal_id_fixo,))
        else:
            cursor.execute("SELECT id, nome, cpf, plano FROM alunos")
        alunos = cursor.fetchall()
        conexao.close()

        for a in alunos:
            tabela_alunos.insert("", "end", iid=str(a[0]), values=(a[1], a[2], a[3] or "-"))

        tk.Label(janela, text="2. Treinos do aluno selecionado", font=FONTE_LABEL_NEGRITO, bg=COR_FUNDO,
                 fg=COR_TEXTO).pack(anchor="w", padx=24, pady=(14, 0))
        tabela_treinos = self.criar_tabela(janela, ("Dia", "Tipo", "Descricao"), altura=8)
        tabela_treinos.column("Descricao", width=300)

        def carregar_treinos():
            for item in tabela_treinos.get_children():
                tabela_treinos.delete(item)
            if not estado["aluno_id"]:
                return
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute("""
                SELECT id, dia_semana, tipo_treino, descricao FROM treinos
                WHERE aluno_id = ?
                ORDER BY CASE dia_semana
                    WHEN 'Segunda-feira' THEN 1 WHEN 'Terca-feira' THEN 2
                    WHEN 'Quarta-feira' THEN 3 WHEN 'Quinta-feira' THEN 4
                    WHEN 'Sexta-feira' THEN 5 WHEN 'Sabado' THEN 6
                    WHEN 'Domingo' THEN 7 ELSE 8 END
            """, (estado["aluno_id"],))
            for t in cursor.fetchall():
                descricao = (t[3] or "").replace("\n", " ")
                tabela_treinos.insert("", "end", iid=str(t[0]),
                                      values=(t[1] or "Sem dia definido", t[2] or "-", descricao))
            conexao.close()

        def selecionar_aluno(_event=None):
            selecao = tabela_alunos.selection()
            if not selecao:
                return
            estado["aluno_id"] = selecao[0]
            carregar_treinos()

        tabela_alunos.bind("<<TreeviewSelect>>", selecionar_aluno)

        def abrir_formulario_treino(treino_existente=None):
            if not estado["aluno_id"]:
                messagebox.showerror("Erro", "Selecione um aluno primeiro.", parent=janela)
                return

            titulo = "Editar Treino" if treino_existente else "Novo Treino"
            modal, f, rodape_modal = self.criar_janela_form(titulo, 440, 520)
            modal.transient(janela)
            try:
                modal.wait_visibility()
                modal.grab_set()
            except tk.TclError:
                pass

            tk.Label(f, text="Tipo de treino (ex: Musculacao, Cardio, Funcional):", font=FONTE_LABEL,
                     bg=COR_FUNDO_CARD).pack(anchor="w", pady=(4, 2))
            entry_tipo = tk.Entry(f, width=36, font=FONTE_LABEL, relief="solid", bd=1)
            entry_tipo.pack(anchor="w", ipady=3)

            tk.Label(f, text="Dia da semana:", font=FONTE_LABEL, bg=COR_FUNDO_CARD).pack(anchor="w", pady=(10, 2))
            dia_selecionado = tk.StringVar(modal)
            combo_dia = ttk.Combobox(f, textvariable=dia_selecionado, values=DIAS_DA_SEMANA,
                                     state="readonly", width=33)
            combo_dia.pack(anchor="w")

            tk.Label(f, text="Descricao do treino:", font=FONTE_LABEL, bg=COR_FUNDO_CARD).pack(anchor="w", pady=(10, 2))
            texto_descricao = tk.Text(f, width=38, height=7, font=FONTE_LABEL, relief="solid", bd=1)
            texto_descricao.pack(anchor="w")

            if treino_existente:
                _id, tipo_atual, dia_atual, descricao_atual = treino_existente
                entry_tipo.insert(0, tipo_atual or "")
                dia_selecionado.set(dia_atual or DIAS_DA_SEMANA[0])
                texto_descricao.insert("1.0", descricao_atual or "")
            else:
                dia_selecionado.set(DIAS_DA_SEMANA[0])

            def salvar():
                tipo_treino = entry_tipo.get().strip()
                dia_semana = dia_selecionado.get()
                descricao = texto_descricao.get("1.0", tk.END).strip()

                if tipo_treino == "":
                    messagebox.showerror("Erro", "Informe o tipo de treino.", parent=modal)
                    return

                conexao = conectar()
                cursor = conexao.cursor()

                cursor.execute("SELECT personal_id FROM alunos WHERE id = ?", (estado["aluno_id"],))
                dono_aluno = cursor.fetchone()
                if not dono_aluno or not dono_aluno[0]:
                    messagebox.showerror("Erro", "Esse aluno ainda nao tem um funcionario atribuido.",
                                         parent=modal)
                    conexao.close()
                    return
                if personal_id_fixo and dono_aluno[0] != personal_id_fixo:
                    messagebox.showerror("Erro", "Esse aluno nao e seu.", parent=modal)
                    conexao.close()
                    return

                if treino_existente:
                    cursor.execute("""
                        UPDATE treinos SET tipo_treino = ?, dia_semana = ?, descricao = ?
                        WHERE id = ?
                    """, (tipo_treino, dia_semana, descricao, treino_existente[0]))
                else:
                    cursor.execute("""
                        INSERT INTO treinos (aluno_id, personal_id, tipo_treino, descricao, dia_semana, data_criacao)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (estado["aluno_id"], dono_aluno[0], tipo_treino, descricao, dia_semana, data_hoje()))

                conexao.commit()
                conexao.close()

                messagebox.showinfo("Sucesso", "Treino salvo com sucesso!", parent=modal)
                modal.destroy()
                carregar_treinos()

            self.botao(rodape_modal, "Salvar", salvar, cor=COR_SUCESSO).pack(side="left", padx=(0, 8))
            self.botao(rodape_modal, "Cancelar", modal.destroy, cor=COR_NEUTRO).pack(side="left")

        def novo_treino():
            abrir_formulario_treino(None)

        def editar_treino():
            selecao = tabela_treinos.selection()
            if not selecao:
                messagebox.showerror("Erro", "Selecione um treino na tabela para editar.", parent=janela)
                return
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute("SELECT id, tipo_treino, dia_semana, descricao FROM treinos WHERE id = ?",
                           (int(selecao[0]),))
            treino = cursor.fetchone()
            conexao.close()
            if not treino:
                messagebox.showerror("Erro", "Treino nao encontrado.", parent=janela)
                return
            abrir_formulario_treino(treino)

        def excluir_treino():
            selecao = tabela_treinos.selection()
            if not selecao:
                messagebox.showerror("Erro", "Selecione um treino na tabela para excluir.", parent=janela)
                return
            treino_id = int(selecao[0])

            if personal_id_fixo:
                conexao = conectar()
                cursor = conexao.cursor()
                cursor.execute("SELECT personal_id FROM treinos WHERE id = ?", (treino_id,))
                dono = cursor.fetchone()
                conexao.close()
                if not dono or dono[0] != personal_id_fixo:
                    messagebox.showerror("Erro", "Esse treino nao e seu.", parent=janela)
                    return

            if not messagebox.askyesno("Confirmar exclusao", "Tem certeza que deseja excluir esse treino?",
                                       parent=janela):
                return

            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM treinos WHERE id = ?", (treino_id,))
            conexao.commit()
            conexao.close()

            messagebox.showinfo("Sucesso", "Treino excluido com sucesso!", parent=janela)
            carregar_treinos()

        self.botao(rodape, "Novo Treino", novo_treino, cor=COR_SUCESSO).pack(side="left", padx=(0, 6))
        self.botao(rodape, "Editar Treino", editar_treino, cor=COR_SECUNDARIA).pack(side="left", padx=(0, 6))
        self.botao(rodape, "Excluir Treino", excluir_treino, cor=COR_PERIGO).pack(side="left", padx=(0, 6))
        self.botao(rodape, "Atualizar", carregar_treinos, cor=COR_NEUTRO).pack(side="left", padx=(0, 6))
        self.botao(rodape, "Fechar", janela.destroy, cor=COR_NEUTRO).pack(side="right")

        if alunos:
            primeiro_iid = str(alunos[0][0])
            tabela_alunos.selection_set(primeiro_iid)
            tabela_alunos.focus(primeiro_iid)
            estado["aluno_id"] = primeiro_iid
            carregar_treinos()

    # ==========================================================
    # AGENDAMENTO DE AULAS
    # ==========================================================
    def abrir_agendar_aula(self, personal_id_fixo):
        janela, rodape = self.criar_janela_rodape("Agendar Aula", 480, 620)

        tk.Label(janela, text="Agendar Aula", font=FONTE_SECAO, bg=COR_FUNDO,
                 fg=COR_PRIMARIA_ESCURA).pack(pady=(16, 6))

        tk.Label(janela, text="Selecione o aluno:", font=FONTE_LABEL, bg=COR_FUNDO).pack(anchor="w", padx=24)
        tabela_alunos = self.criar_tabela(janela, ("Nome", "CPF"), altura=6)

        conexao = conectar()
        cursor = conexao.cursor()
        if personal_id_fixo:
            cursor.execute("SELECT id, nome, cpf FROM alunos WHERE personal_id = ?", (personal_id_fixo,))
        else:
            cursor.execute("SELECT id, nome, cpf FROM alunos")
        for a in cursor.fetchall():
            tabela_alunos.insert("", "end", iid=str(a[0]), values=(a[1], a[2]))
        conexao.close()

        moldura = tk.Frame(janela, bg=COR_FUNDO_CARD, highlightthickness=1, highlightbackground=COR_BORDA)
        moldura.pack(fill="x", padx=24, pady=10)
        f = tk.Frame(moldura, bg=COR_FUNDO_CARD)
        f.pack(fill="x", padx=16, pady=12)

        entry_data = self.campo_form(f, "Data da aula (dd/mm/aaaa):", largura=20)
        entry_data.bind("<KeyRelease>", formatar_data)
        entry_horario = self.campo_form(f, "Horario (hh:mm):", largura=20)
        entry_horario.bind("<KeyRelease>", formatar_hora)

        def salvar_agendamento():
            selecao = tabela_alunos.selection()
            if not selecao:
                messagebox.showerror("Erro", "Selecione um aluno.", parent=janela)
                return
            aluno_id = selecao[0]

            data_aula = entry_data.get().strip()
            horario = entry_horario.get().strip()
            try:
                datetime.strptime(data_aula, "%d/%m/%Y")
            except ValueError:
                messagebox.showerror("Erro", "Data invalida. Use o formato dd/mm/aaaa.", parent=janela)
                return
            try:
                datetime.strptime(horario, "%H:%M")
            except ValueError:
                messagebox.showerror("Erro", "Horario invalido. Use o formato hh:mm.", parent=janela)
                return

            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute("SELECT personal_id FROM alunos WHERE id = ?", (aluno_id,))
            aluno = cursor.fetchone()

            if not aluno or not aluno[0]:
                messagebox.showerror("Erro", "Esse aluno nao tem funcionario atribuido.", parent=janela)
                conexao.close()
                return
            if personal_id_fixo and aluno[0] != personal_id_fixo:
                messagebox.showerror("Erro", "Esse aluno nao e seu.", parent=janela)
                conexao.close()
                return

            cursor.execute("""
                INSERT INTO agendamentos (aluno_id, personal_id, data_aula, horario, status)
                VALUES (?, ?, ?, ?, 'AGENDADA')
            """, (aluno_id, aluno[0], data_aula, horario))
            conexao.commit()
            conexao.close()

            messagebox.showinfo("Sucesso", "Aula agendada com sucesso!", parent=janela)
            janela.destroy()

        self.botao(rodape, "Agendar", salvar_agendamento, cor=COR_SUCESSO).pack(side="left", padx=(0, 8))
        self.botao(rodape, "Cancelar", janela.destroy, cor=COR_NEUTRO).pack(side="left")

    def abrir_ver_agendamentos(self, personal_id_fixo):
        conexao = conectar()
        cursor = conexao.cursor()
        base = """
            SELECT agendamentos.id, alunos.nome, personais.nome, agendamentos.data_aula,
                   agendamentos.horario, agendamentos.status
            FROM agendamentos
            JOIN alunos ON agendamentos.aluno_id = alunos.id
            JOIN personais ON agendamentos.personal_id = personais.id
        """
        if personal_id_fixo:
            cursor.execute(base + " WHERE agendamentos.personal_id = ? "
                           "ORDER BY agendamentos.data_aula, agendamentos.horario", (personal_id_fixo,))
        else:
            cursor.execute(base + " ORDER BY agendamentos.data_aula, agendamentos.horario")
        resultado = cursor.fetchall()
        conexao.close()

        linhas = [(ag[0], (ag[1], ag[2], ag[3], ag[4], ag[5])) for ag in resultado]
        self.janela_lista("Lista de Agendamentos", 720, 500,
                          ("Aluno", "Funcionario", "Data", "Horario", "Status"), linhas,
                          "Nenhuma aula agendada.")

    # ==========================================================
    # COBRANCA DE MENSALIDADE
    # ==========================================================
    def gerar_cobrancas_do_mes(self):
        hoje = datetime.now()
        mes_referencia = hoje.strftime("%m/%Y")
        vencimento = f"10/{hoje.strftime('%m/%Y')}"

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, nome, valor_mensalidade FROM alunos")
        alunos = cursor.fetchall()

        total_geradas = 0
        mensagem = ""

        for aluno_id, nome, valor in alunos:
            valor = valor or 0.0
            cursor.execute("SELECT id FROM pagamentos WHERE aluno_id = ? AND mes_referencia = ?",
                           (aluno_id, mes_referencia))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO pagamentos (aluno_id, valor, mes_referencia, data_vencimento, status)
                    VALUES (?, ?, ?, ?, 'PENDENTE')
                """, (aluno_id, valor, mes_referencia, vencimento))
                total_geradas += 1
                mensagem += f"Cobranca gerada para {nome} - R$ {valor:.2f}\n"

        conexao.commit()
        conexao.close()

        if total_geradas == 0:
            messagebox.showinfo("Cobrancas", "Nenhuma cobranca nova para gerar (todas ja foram geradas esse mes).")
        else:
            messagebox.showinfo("Cobrancas", f"{mensagem}\nTotal de {total_geradas} cobranca(s) gerada(s).")

    def verificar_cobranca_automatica(self):
        hoje = datetime.now()
        if hoje.day != 10:
            return

        mes_referencia = hoje.strftime("%m/%Y")
        vencimento = f"10/{hoje.strftime('%m/%Y')}"

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, valor_mensalidade FROM alunos")
        alunos = cursor.fetchall()

        gerou_alguma = False
        for aluno_id, valor in alunos:
            cursor.execute("SELECT id FROM pagamentos WHERE aluno_id = ? AND mes_referencia = ?",
                           (aluno_id, mes_referencia))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO pagamentos (aluno_id, valor, mes_referencia, data_vencimento, status)
                    VALUES (?, ?, ?, ?, 'PENDENTE')
                """, (aluno_id, valor or 0.0, mes_referencia, vencimento))
                gerou_alguma = True

        conexao.commit()
        conexao.close()

        if gerou_alguma:
            messagebox.showinfo("Cobranca Automatica",
                                "Hoje e dia 10! As cobrancas do mes foram geradas automaticamente.")

    def abrir_ver_pagamentos(self):
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT pagamentos.id, alunos.nome, pagamentos.valor, pagamentos.mes_referencia,
                   pagamentos.data_vencimento, pagamentos.status
            FROM pagamentos
            JOIN alunos ON pagamentos.aluno_id = alunos.id
            ORDER BY substr(pagamentos.mes_referencia, 4, 4) DESC,
                     substr(pagamentos.mes_referencia, 1, 2) DESC
        """)
        resultado = cursor.fetchall()
        conexao.close()

        linhas = [(p[0], (p[1], f"R$ {(p[2] or 0):.2f}", p[3], p[4], p[5])) for p in resultado]
        self.janela_lista("Lista de Pagamentos", 720, 500,
                          ("Aluno", "Valor", "Mes", "Vencimento", "Status"), linhas,
                          "Nenhum pagamento registrado ainda.")

    def abrir_marcar_pagamento(self):
        janela, rodape = self.criar_janela_rodape("Marcar Pagamento como Pago", 580, 500)

        tk.Label(janela, text="Marcar Pagamento como Pago", font=FONTE_SECAO, bg=COR_FUNDO,
                 fg=COR_PRIMARIA_ESCURA).pack(pady=(16, 6))
        tk.Label(janela, text="Selecione o pagamento pendente:", font=FONTE_LABEL,
                 bg=COR_FUNDO).pack(anchor="w", padx=24)

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT pagamentos.id, alunos.nome, pagamentos.valor, pagamentos.mes_referencia, pagamentos.status
            FROM pagamentos
            JOIN alunos ON pagamentos.aluno_id = alunos.id
            WHERE pagamentos.status = 'PENDENTE'
            ORDER BY substr(pagamentos.mes_referencia, 4, 4) DESC,
                     substr(pagamentos.mes_referencia, 1, 2) DESC
        """)
        pendentes = cursor.fetchall()
        conexao.close()

        if not pendentes:
            tk.Label(janela, text="Nenhum pagamento pendente.", bg=COR_FUNDO,
                     fg=COR_NEUTRO, font=FONTE_LABEL).pack(pady=4)

        tabela = self.criar_tabela(janela, ("Aluno", "Valor", "Mes", "Status"), altura=10)
        for p in pendentes:
            tabela.insert("", "end", iid=str(p[0]),
                          values=(p[1], f"R$ {(p[2] or 0):.2f}", p[3], p[4]))

        def salvar_pagamento():
            selecao = tabela.selection()
            if not selecao:
                messagebox.showerror("Erro", "Selecione um pagamento na tabela.", parent=janela)
                return

            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute("""
                UPDATE pagamentos SET status = 'PAGO', data_pagamento = ? WHERE id = ?
            """, (data_hoje(), selecao[0]))
            conexao.commit()
            conexao.close()

            messagebox.showinfo("Sucesso", "Pagamento marcado como PAGO com sucesso!", parent=janela)
            janela.destroy()

        self.botao(rodape, "Marcar como Pago", salvar_pagamento, cor=COR_SUCESSO).pack(side="left", padx=(0, 8))
        self.botao(rodape, "Cancelar", janela.destroy, cor=COR_NEUTRO).pack(side="left")


# ==========================================================
# INICIO DO PROGRAMA
# ==========================================================

if __name__ == "__main__":
    app = AcademiaApp()
    app.mainloop()