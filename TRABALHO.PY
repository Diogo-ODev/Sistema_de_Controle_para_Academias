"""
SISTEMA DE GESTAO DE ACADEMIA - COM TELAS E LOGIN (TKINTER)

Fluxo do sistema:
1) Tela de Cadastro da Academia (aparece so na primeira vez que o sistema roda)
2) Tela de Login (Dono / Funcionario / Aluno)
3) Depois do login, cada tipo de usuario ve uma tela diferente:
   - DONO: acesso total (cadastra funcionarios, alunos, treinos, aulas, cobrancas...)
   - FUNCIONARIO (Personal): ve e cuida apenas dos ALUNOS DELE
   - ALUNO: ve apenas os PROPRIOS TREINOS, separados por dia da semana

Feito em Python puro com Tkinter e SQLite (bibliotecas padrao, nao precisa
instalar nada).
"""

import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

NOME_BANCO = "academia.db"

DIAS_DA_SEMANA = [
    "Segunda-feira", "Terca-feira", "Quarta-feira",
    "Quinta-feira", "Sexta-feira", "Sabado", "Domingo"
]


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
            data_cadastro TEXT
        )
    """)

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
# USUARIO LOGADO (variaveis globais simples)
# ==========================================================

usuario_logado_tipo = None       # "dono", "funcionario" ou "aluno"
usuario_logado_id = None         # id do personal ou do aluno (dono nao precisa)
usuario_logado_nome = None


# ==========================================================
# JANELA PRINCIPAL E TROCA DE TELAS
# ==========================================================

janela_principal = tk.Tk()
janela_principal.title("Sistema de Gestao de Academia")
janela_principal.geometry("450x650")
janela_principal.configure(bg="lightblue")


def limpar_tela():
    for widget in janela_principal.winfo_children():
        widget.destroy()


# ==========================================================
# TELA 1 - CADASTRO DA ACADEMIA (so aparece na primeira vez)
# ==========================================================

def tela_cadastro_academia():
    limpar_tela()

    tk.Label(janela_principal, text="BEM-VINDO!", font=("Arial", 20, "bold"),
             bg="lightblue", fg="darkblue").pack(pady=10)
    tk.Label(janela_principal, text="Vamos cadastrar sua academia", font=("Arial", 12),
             bg="lightblue").pack(pady=(0, 15))

    tk.Label(janela_principal, text="Nome da academia:", bg="lightblue").pack()
    entry_nome = tk.Entry(janela_principal, width=35)
    entry_nome.pack()

    tk.Label(janela_principal, text="CNPJ:", bg="lightblue").pack()
    entry_cnpj = tk.Entry(janela_principal, width=35)
    entry_cnpj.pack()

    tk.Label(janela_principal, text="Telefone:", bg="lightblue").pack()
    entry_telefone = tk.Entry(janela_principal, width=35)
    entry_telefone.pack()

    tk.Label(janela_principal, text="Endereco:", bg="lightblue").pack()
    entry_endereco = tk.Entry(janela_principal, width=35)
    entry_endereco.pack()

    tk.Label(janela_principal, text="Email do dono (sera seu login):", bg="lightblue").pack()
    entry_email = tk.Entry(janela_principal, width=35)
    entry_email.pack()

    tk.Label(janela_principal, text="Senha do dono:", bg="lightblue").pack()
    entry_senha = tk.Entry(janela_principal, width=35, show="*")
    entry_senha.pack()

    def salvar_academia():
        nome = entry_nome.get()
        email = entry_email.get()
        senha = entry_senha.get()

        if nome == "" or email == "" or senha == "":
            messagebox.showerror("Erro", "Nome, email e senha sao obrigatorios.")
            return

        conexao = conectar()
        cursor = conexao.cursor()
        try:
            cursor.execute("""
                INSERT INTO academia (nome, cnpj, telefone, email, endereco, senha, data_cadastro)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nome, entry_cnpj.get(), entry_telefone.get(), email,
                  entry_endereco.get(), senha, data_hoje()))
            conexao.commit()
            messagebox.showinfo("Sucesso", "Academia cadastrada com sucesso!\nAgora faca login como Dono.")
            tela_login()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Ja existe uma academia cadastrada com esse email.")
        finally:
            conexao.close()

    tk.Button(janela_principal, text="Cadastrar Academia", command=salvar_academia,
              bg="lightgreen", width=20).pack(pady=20)


# ==========================================================
# TELA 2 - LOGIN
# ==========================================================

def tela_login():
    limpar_tela()
    global usuario_logado_tipo, usuario_logado_id, usuario_logado_nome
    usuario_logado_tipo = None
    usuario_logado_id = None
    usuario_logado_nome = None

    tk.Label(janela_principal, text="ACADEMIA FIT", font=("Arial", 22, "bold"),
             bg="lightblue", fg="darkblue").pack(pady=20)
    tk.Label(janela_principal, text="Escolha o tipo de acesso:", font=("Arial", 12),
             bg="lightblue").pack(pady=10)

    tk.Button(janela_principal, text="Sou o Dono da Academia", width=30, bg="white",
              command=lambda: tela_formulario_login("dono")).pack(pady=8)
    tk.Button(janela_principal, text="Sou Funcionario (Personal)", width=30, bg="white",
              command=lambda: tela_formulario_login("funcionario")).pack(pady=8)
    tk.Button(janela_principal, text="Sou Aluno", width=30, bg="white",
              command=lambda: tela_formulario_login("aluno")).pack(pady=8)


def tela_formulario_login(tipo):
    limpar_tela()

    titulos = {
        "dono": "LOGIN - DONO DA ACADEMIA",
        "funcionario": "LOGIN - FUNCIONARIO",
        "aluno": "LOGIN - ALUNO"
    }

    tk.Label(janela_principal, text=titulos[tipo], font=("Arial", 16, "bold"),
             bg="lightblue", fg="darkblue").pack(pady=20)

    if tipo == "dono":
        tk.Label(janela_principal, text="Email:", bg="lightblue").pack()
    else:
        tk.Label(janela_principal, text="CPF:", bg="lightblue").pack()

    entry_login = tk.Entry(janela_principal, width=30)
    entry_login.pack(pady=5)

    tk.Label(janela_principal, text="Senha:", bg="lightblue").pack()
    entry_senha = tk.Entry(janela_principal, width=30, show="*")
    entry_senha.pack(pady=5)

    def entrar():
        valor_login = entry_login.get()
        senha = entry_senha.get()

        conexao = conectar()
        cursor = conexao.cursor()

        if tipo == "dono":
            cursor.execute("SELECT id, nome, senha FROM academia WHERE email = ?", (valor_login,))
        elif tipo == "funcionario":
            cursor.execute("SELECT id, nome, senha FROM personais WHERE cpf = ?", (valor_login,))
        else:
            cursor.execute("SELECT id, nome, senha FROM alunos WHERE cpf = ?", (valor_login,))

        resultado = cursor.fetchone()
        conexao.close()

        if not resultado:
            messagebox.showerror("Erro", "Usuario nao encontrado.")
            return

        id_encontrado, nome_encontrado, senha_encontrada = resultado

        if senha != senha_encontrada:
            messagebox.showerror("Erro", "Senha incorreta.")
            return

        global usuario_logado_tipo, usuario_logado_id, usuario_logado_nome
        usuario_logado_tipo = tipo
        usuario_logado_id = id_encontrado
        usuario_logado_nome = nome_encontrado

        if tipo == "dono":
            tela_dono()
        elif tipo == "funcionario":
            tela_funcionario()
        else:
            tela_aluno()

    tk.Button(janela_principal, text="Entrar", command=entrar, bg="lightgreen", width=15).pack(pady=15)
    tk.Button(janela_principal, text="Voltar", command=tela_login, bg="salmon", width=15).pack()


# ==========================================================
# TELA DO DONO (acesso total)
# ==========================================================

def tela_dono():
    limpar_tela()

    tk.Label(janela_principal, text=f"Bem-vindo, {usuario_logado_nome}", font=("Arial", 14, "bold"),
             bg="lightblue", fg="darkblue").pack(pady=5)
    tk.Label(janela_principal, text="(Acesso: DONO DA ACADEMIA)", bg="lightblue").pack(pady=(0, 15))

    tk.Button(janela_principal, text="Cadastrar Funcionario", width=32, command=abrir_cadastro_personal).pack(pady=3)
    tk.Button(janela_principal, text="Listar Funcionarios", width=32, command=abrir_lista_personais).pack(pady=3)
    tk.Button(janela_principal, text="Cadastrar Aluno", width=32, command=abrir_cadastro_aluno).pack(pady=3)
    tk.Button(janela_principal, text="Listar Alunos", width=32, command=abrir_lista_alunos).pack(pady=3)
    tk.Button(janela_principal, text="Atribuir Aluno a um Funcionario", width=32,
              command=abrir_atribuir_personal).pack(pady=3)
    tk.Button(janela_principal, text="Definir Treino do Aluno", width=32,
              command=lambda: abrir_definir_treino(None)).pack(pady=3)
    tk.Button(janela_principal, text="Ver Treinos de um Aluno", width=32,
              command=lambda: abrir_ver_treinos(None)).pack(pady=3)
    tk.Button(janela_principal, text="Agendar Aula", width=32,
              command=lambda: abrir_agendar_aula(None)).pack(pady=3)
    tk.Button(janela_principal, text="Ver Agendamentos", width=32,
              command=lambda: abrir_ver_agendamentos(None)).pack(pady=3)
    tk.Button(janela_principal, text="Gerar Cobrancas do Mes", width=32,
              command=gerar_cobrancas_do_mes).pack(pady=3)
    tk.Button(janela_principal, text="Ver Pagamentos", width=32, command=abrir_ver_pagamentos).pack(pady=3)
    tk.Button(janela_principal, text="Marcar Pagamento como Pago", width=32,
              command=abrir_marcar_pagamento).pack(pady=3)

    tk.Button(janela_principal, text="Sair (Logout)", width=32, bg="salmon", command=tela_login).pack(pady=15)


# ==========================================================
# TELA DO FUNCIONARIO (personal) - so ve os alunos DELE
# ==========================================================

def tela_funcionario():
    limpar_tela()

    tk.Label(janela_principal, text=f"Bem-vindo, {usuario_logado_nome}", font=("Arial", 14, "bold"),
             bg="lightblue", fg="darkblue").pack(pady=5)
    tk.Label(janela_principal, text="(Acesso: FUNCIONARIO / PERSONAL)", bg="lightblue").pack(pady=(0, 15))

    tk.Button(janela_principal, text="Ver Meus Alunos", width=32, command=abrir_meus_alunos).pack(pady=5)
    tk.Button(janela_principal, text="Definir Treino de um Aluno Meu", width=32,
              command=lambda: abrir_definir_treino(usuario_logado_id)).pack(pady=5)
    tk.Button(janela_principal, text="Ver Treinos de um Aluno Meu", width=32,
              command=lambda: abrir_ver_treinos(usuario_logado_id)).pack(pady=5)
    tk.Button(janela_principal, text="Agendar Aula com um Aluno Meu", width=32,
              command=lambda: abrir_agendar_aula(usuario_logado_id)).pack(pady=5)
    tk.Button(janela_principal, text="Ver Meus Agendamentos", width=32,
              command=lambda: abrir_ver_agendamentos(usuario_logado_id)).pack(pady=5)

    tk.Button(janela_principal, text="Sair (Logout)", width=32, bg="salmon", command=tela_login).pack(pady=20)


def abrir_meus_alunos():
    janela = tk.Toplevel(janela_principal)
    janela.title("Meus Alunos")
    janela.geometry("450x400")

    tk.Label(janela, text="MEUS ALUNOS", font=("Arial", 12, "bold")).pack(pady=10)

    caixa_texto = tk.Text(janela, width=55, height=18)
    caixa_texto.pack(padx=10, pady=10)

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT id, nome, cpf, plano FROM alunos WHERE personal_id = ?
    """, (usuario_logado_id,))
    resultado = cursor.fetchall()
    conexao.close()

    if len(resultado) == 0:
        caixa_texto.insert(tk.END, "Voce ainda nao tem alunos atribuidos.")
    else:
        for a in resultado:
            caixa_texto.insert(tk.END, f"ID: {a[0]} | Nome: {a[1]}\nCPF: {a[2]} | Plano: {a[3]}\n\n")


# ==========================================================
# TELA DO ALUNO - so ve os PROPRIOS treinos, por dia da semana
# ==========================================================

def tela_aluno():
    limpar_tela()

    tk.Label(janela_principal, text=f"Bem-vindo, {usuario_logado_nome}", font=("Arial", 14, "bold"),
             bg="lightblue", fg="darkblue").pack(pady=5)
    tk.Label(janela_principal, text="(Acesso: ALUNO)", bg="lightblue").pack(pady=(0, 15))

    tk.Button(janela_principal, text="Meus Treinos por Dia", width=32,
              command=abrir_meus_treinos_por_dia).pack(pady=5)
    tk.Button(janela_principal, text="Meus Proximos Agendamentos", width=32,
              command=abrir_meus_agendamentos).pack(pady=5)

    tk.Button(janela_principal, text="Sair (Logout)", width=32, bg="salmon", command=tela_login).pack(pady=20)


def abrir_meus_treinos_por_dia():
    janela = tk.Toplevel(janela_principal)
    janela.title("Meus Treinos por Dia")
    janela.geometry("480x500")

    tk.Label(janela, text="MEUS TREINOS - POR DIA DA SEMANA", font=("Arial", 12, "bold")).pack(pady=10)

    caixa_texto = tk.Text(janela, width=58, height=22)
    caixa_texto.pack(padx=10, pady=10)

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT tipo_treino, descricao, dia_semana FROM treinos WHERE aluno_id = ?
    """, (usuario_logado_id,))
    treinos = cursor.fetchall()
    conexao.close()

    if len(treinos) == 0:
        caixa_texto.insert(tk.END, "Voce ainda nao tem treinos cadastrados.")
        return

    for dia in DIAS_DA_SEMANA:
        treinos_do_dia = [t for t in treinos if t[2] == dia]
        if treinos_do_dia:
            caixa_texto.insert(tk.END, f"=== {dia.upper()} ===\n")
            for t in treinos_do_dia:
                caixa_texto.insert(tk.END, f"- Tipo: {t[0]}\n  Descricao: {t[1]}\n\n")

    treinos_sem_dia = [t for t in treinos if not t[2]]
    if treinos_sem_dia:
        caixa_texto.insert(tk.END, "=== SEM DIA DEFINIDO ===\n")
        for t in treinos_sem_dia:
            caixa_texto.insert(tk.END, f"- Tipo: {t[0]}\n  Descricao: {t[1]}\n\n")


def abrir_meus_agendamentos():
    janela = tk.Toplevel(janela_principal)
    janela.title("Meus Agendamentos")
    janela.geometry("450x400")

    tk.Label(janela, text="MEUS PROXIMOS AGENDAMENTOS", font=("Arial", 12, "bold")).pack(pady=10)

    caixa_texto = tk.Text(janela, width=55, height=18)
    caixa_texto.pack(padx=10, pady=10)

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT agendamentos.data_aula, agendamentos.horario, personais.nome, agendamentos.status
        FROM agendamentos
        JOIN personais ON agendamentos.personal_id = personais.id
        WHERE agendamentos.aluno_id = ?
        ORDER BY agendamentos.data_aula, agendamentos.horario
    """, (usuario_logado_id,))
    resultado = cursor.fetchall()
    conexao.close()

    if len(resultado) == 0:
        caixa_texto.insert(tk.END, "Voce nao tem nenhuma aula agendada.")
    else:
        for ag in resultado:
            caixa_texto.insert(tk.END, f"Data: {ag[0]} | Horario: {ag[1]}\nPersonal: {ag[2]} | Status: {ag[3]}\n\n")


# ==========================================================
# CADASTRO DE FUNCIONARIO (PERSONAL) - so o Dono acessa
# ==========================================================

def abrir_cadastro_personal():
    janela = tk.Toplevel(janela_principal)
    janela.title("Cadastrar Funcionario")
    janela.geometry("350x580")

    tk.Label(janela, text="CADASTRO DE FUNCIONARIO (PERSONAL)", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(janela, text="Nome completo:").pack()
    entry_nome = tk.Entry(janela, width=35)
    entry_nome.pack()

    tk.Label(janela, text="CPF (sera o login dele):").pack()
    entry_cpf = tk.Entry(janela, width=35)
    entry_cpf.pack()

    tk.Label(janela, text="Senha de acesso:").pack()
    entry_senha = tk.Entry(janela, width=35, show="*")
    entry_senha.pack()

    tk.Label(janela, text="Data de nascimento (dd/mm/aaaa):").pack()
    entry_nasc = tk.Entry(janela, width=35)
    entry_nasc.pack()

    tk.Label(janela, text="Telefone:").pack()
    entry_tel = tk.Entry(janela, width=35)
    entry_tel.pack()

    tk.Label(janela, text="Email:").pack()
    entry_email = tk.Entry(janela, width=35)
    entry_email.pack()

    tk.Label(janela, text="Endereco:").pack()
    entry_end = tk.Entry(janela, width=35)
    entry_end.pack()

    tk.Label(janela, text="Numero do CREF:").pack()
    entry_cref = tk.Entry(janela, width=35)
    entry_cref.pack()

    tk.Label(janela, text="Especialidade:").pack()
    entry_esp = tk.Entry(janela, width=35)
    entry_esp.pack()

    def salvar_personal():
        nome = entry_nome.get()
        cpf = entry_cpf.get()
        senha = entry_senha.get()

        if nome == "" or cpf == "" or senha == "":
            messagebox.showerror("Erro", "Nome, CPF e senha sao obrigatorios.")
            return

        conexao = conectar()
        cursor = conexao.cursor()
        try:
            cursor.execute("""
                INSERT INTO personais
                (nome, cpf, senha, data_nascimento, telefone, email, endereco, cref, especialidade, data_cadastro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (nome, cpf, senha, entry_nasc.get(), entry_tel.get(), entry_email.get(),
                  entry_end.get(), entry_cref.get(), entry_esp.get(), data_hoje()))
            conexao.commit()
            messagebox.showinfo("Sucesso", "Funcionario cadastrado com sucesso! ID: " + str(cursor.lastrowid))
            janela.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Ja existe um funcionario cadastrado com esse CPF.")
        finally:
            conexao.close()

    tk.Button(janela, text="Salvar", command=salvar_personal, bg="lightgreen", width=15).pack(pady=15)


def abrir_lista_personais():
    janela = tk.Toplevel(janela_principal)
    janela.title("Lista de Funcionarios")
    janela.geometry("450x400")

    tk.Label(janela, text="LISTA DE FUNCIONARIOS", font=("Arial", 12, "bold")).pack(pady=10)

    caixa_texto = tk.Text(janela, width=55, height=18)
    caixa_texto.pack(padx=10, pady=10)

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome, cpf, telefone, especialidade FROM personais")
    resultado = cursor.fetchall()
    conexao.close()

    if len(resultado) == 0:
        caixa_texto.insert(tk.END, "Nenhum funcionario cadastrado.")
    else:
        for p in resultado:
            caixa_texto.insert(
                tk.END,
                f"ID: {p[0]} | Nome: {p[1]}\nCPF: {p[2]} | Tel: {p[3]}\nEspecialidade: {p[4]}\n\n"
            )


# ==========================================================
# CADASTRO DE ALUNO - so o Dono acessa
# ==========================================================

def abrir_cadastro_aluno():
    janela = tk.Toplevel(janela_principal)
    janela.title("Cadastrar Aluno")
    janela.geometry("350x660")

    tk.Label(janela, text="CADASTRO DE ALUNO", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(janela, text="Nome completo:").pack()
    entry_nome = tk.Entry(janela, width=35)
    entry_nome.pack()

    tk.Label(janela, text="CPF (sera o login dele):").pack()
    entry_cpf = tk.Entry(janela, width=35)
    entry_cpf.pack()

    tk.Label(janela, text="Senha de acesso:").pack()
    entry_senha = tk.Entry(janela, width=35, show="*")
    entry_senha.pack()

    tk.Label(janela, text="Data de nascimento (dd/mm/aaaa):").pack()
    entry_nasc = tk.Entry(janela, width=35)
    entry_nasc.pack()

    tk.Label(janela, text="Telefone:").pack()
    entry_tel = tk.Entry(janela, width=35)
    entry_tel.pack()

    tk.Label(janela, text="Email:").pack()
    entry_email = tk.Entry(janela, width=35)
    entry_email.pack()

    tk.Label(janela, text="Endereco:").pack()
    entry_end = tk.Entry(janela, width=35)
    entry_end.pack()

    tk.Label(janela, text="Objetivo (ex: emagrecimento, hipertrofia):").pack()
    entry_obj = tk.Entry(janela, width=35)
    entry_obj.pack()

    tk.Label(janela, text="Plano (ex: mensal, trimestral, anual):").pack()
    entry_plano = tk.Entry(janela, width=35)
    entry_plano.pack()

    tk.Label(janela, text="Valor da mensalidade (ex: 150.00):").pack()
    entry_valor = tk.Entry(janela, width=35)
    entry_valor.pack()

    def salvar_aluno():
        nome = entry_nome.get()
        cpf = entry_cpf.get()
        senha = entry_senha.get()

        if nome == "" or cpf == "" or senha == "":
            messagebox.showerror("Erro", "Nome, CPF e senha sao obrigatorios.")
            return

        try:
            valor_mensalidade = float(entry_valor.get())
        except ValueError:
            valor_mensalidade = 0.0
            messagebox.showwarning("Aviso", "Valor invalido, foi definido como 0.00. Voce pode corrigir depois.")

        conexao = conectar()
        cursor = conexao.cursor()
        try:
            cursor.execute("""
                INSERT INTO alunos
                (nome, cpf, senha, data_nascimento, telefone, email, endereco, objetivo, plano,
                 valor_mensalidade, personal_id, data_cadastro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
            """, (nome, cpf, senha, entry_nasc.get(), entry_tel.get(), entry_email.get(),
                  entry_end.get(), entry_obj.get(), entry_plano.get(), valor_mensalidade, data_hoje()))
            conexao.commit()
            messagebox.showinfo("Sucesso", "Aluno cadastrado com sucesso! ID: " + str(cursor.lastrowid))
            janela.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Ja existe um aluno cadastrado com esse CPF.")
        finally:
            conexao.close()

    tk.Button(janela, text="Salvar", command=salvar_aluno, bg="lightgreen", width=15).pack(pady=15)


def abrir_lista_alunos():
    janela = tk.Toplevel(janela_principal)
    janela.title("Lista de Alunos")
    janela.geometry("450x400")

    tk.Label(janela, text="LISTA DE ALUNOS", font=("Arial", 12, "bold")).pack(pady=10)

    caixa_texto = tk.Text(janela, width=55, height=18)
    caixa_texto.pack(padx=10, pady=10)

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT alunos.id, alunos.nome, alunos.cpf, alunos.plano, personais.nome
        FROM alunos
        LEFT JOIN personais ON alunos.personal_id = personais.id
    """)
    resultado = cursor.fetchall()
    conexao.close()

    if len(resultado) == 0:
        caixa_texto.insert(tk.END, "Nenhum aluno cadastrado.")
    else:
        for a in resultado:
            nome_personal = a[4] if a[4] else "SEM PERSONAL"
            caixa_texto.insert(
                tk.END,
                f"ID: {a[0]} | Nome: {a[1]}\nCPF: {a[2]} | Plano: {a[3]}\nPersonal: {nome_personal}\n\n"
            )


# ==========================================================
# ATRIBUIR ALUNO A UM FUNCIONARIO - so o Dono acessa
# ==========================================================

def abrir_atribuir_personal():
    janela = tk.Toplevel(janela_principal)
    janela.title("Atribuir Aluno a um Funcionario")
    janela.geometry("400x550")

    tk.Label(janela, text="ATRIBUIR ALUNO A UM FUNCIONARIO", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(janela, text="Alunos cadastrados:").pack()
    caixa_alunos = tk.Text(janela, width=45, height=8)
    caixa_alunos.pack(pady=5)

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome FROM alunos")
    for a in cursor.fetchall():
        caixa_alunos.insert(tk.END, f"{a[0]} - {a[1]}\n")
    conexao.close()

    tk.Label(janela, text="Digite o ID do aluno:").pack()
    entry_aluno_id = tk.Entry(janela, width=10)
    entry_aluno_id.pack()

    tk.Label(janela, text="Funcionarios cadastrados:").pack(pady=(10, 0))
    caixa_personais = tk.Text(janela, width=45, height=8)
    caixa_personais.pack(pady=5)

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome FROM personais")
    for p in cursor.fetchall():
        caixa_personais.insert(tk.END, f"{p[0]} - {p[1]}\n")
    conexao.close()

    tk.Label(janela, text="Digite o ID do funcionario:").pack()
    entry_personal_id = tk.Entry(janela, width=10)
    entry_personal_id.pack()

    def salvar_atribuicao():
        aluno_id = entry_aluno_id.get()
        personal_id = entry_personal_id.get()

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id FROM alunos WHERE id = ?", (aluno_id,))
        aluno = cursor.fetchone()
        cursor.execute("SELECT id FROM personais WHERE id = ?", (personal_id,))
        personal = cursor.fetchone()

        if not aluno:
            messagebox.showerror("Erro", "Aluno nao encontrado.")
        elif not personal:
            messagebox.showerror("Erro", "Funcionario nao encontrado.")
        else:
            cursor.execute("UPDATE alunos SET personal_id = ? WHERE id = ?", (personal_id, aluno_id))
            conexao.commit()
            messagebox.showinfo("Sucesso", "Aluno atribuido ao funcionario com sucesso!")
            janela.destroy()

        conexao.close()

    tk.Button(janela, text="Atribuir", command=salvar_atribuicao, bg="lightgreen", width=15).pack(pady=15)


# ==========================================================
# DEFINIR TREINO DO ALUNO (com dia da semana)
# Se personal_id_fixo for informado (funcionario logado), so pode
# escolher entre os alunos DELE. Se for None (dono), pode escolher qualquer aluno.
# ==========================================================

def abrir_definir_treino(personal_id_fixo):
    janela = tk.Toplevel(janela_principal)
    janela.title("Definir Treino do Aluno")
    janela.geometry("400x600")

    tk.Label(janela, text="DEFINIR TREINO DO ALUNO", font=("Arial", 12, "bold")).pack(pady=10)

    if personal_id_fixo:
        tk.Label(janela, text="Meus alunos:").pack()
    else:
        tk.Label(janela, text="Alunos cadastrados:").pack()

    caixa_alunos = tk.Text(janela, width=45, height=8)
    caixa_alunos.pack(pady=5)

    conexao = conectar()
    cursor = conexao.cursor()
    if personal_id_fixo:
        cursor.execute("SELECT id, nome FROM alunos WHERE personal_id = ?", (personal_id_fixo,))
    else:
        cursor.execute("SELECT id, nome FROM alunos")
    for a in cursor.fetchall():
        caixa_alunos.insert(tk.END, f"{a[0]} - {a[1]}\n")
    conexao.close()

    tk.Label(janela, text="Digite o ID do aluno:").pack()
    entry_aluno_id = tk.Entry(janela, width=10)
    entry_aluno_id.pack()

    tk.Label(janela, text="Tipo de treino (ex: Musculacao, Cardio, Funcional):").pack(pady=(10, 0))
    entry_tipo = tk.Entry(janela, width=35)
    entry_tipo.pack()

    tk.Label(janela, text="Dia da semana desse treino:").pack(pady=(10, 0))
    dia_selecionado = tk.StringVar(janela)
    dia_selecionado.set(DIAS_DA_SEMANA[0])
    tk.OptionMenu(janela, dia_selecionado, *DIAS_DA_SEMANA).pack()

    tk.Label(janela, text="Descricao do treino:").pack(pady=(10, 0))
    texto_descricao = tk.Text(janela, width=40, height=6)
    texto_descricao.pack()

    def salvar_treino():
        aluno_id = entry_aluno_id.get()

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, personal_id FROM alunos WHERE id = ?", (aluno_id,))
        aluno = cursor.fetchone()

        if not aluno:
            messagebox.showerror("Erro", "Aluno nao encontrado.")
            conexao.close()
            return

        if not aluno[1]:
            messagebox.showerror("Erro", "Esse aluno ainda nao tem um funcionario atribuido.")
            conexao.close()
            return

        # se for funcionario logado, so pode mexer nos proprios alunos
        if personal_id_fixo and aluno[1] != personal_id_fixo:
            messagebox.showerror("Erro", "Esse aluno nao e seu. Voce so pode definir treinos dos seus alunos.")
            conexao.close()
            return

        personal_id = aluno[1]
        tipo_treino = entry_tipo.get()
        dia_semana = dia_selecionado.get()
        descricao = texto_descricao.get("1.0", tk.END).strip()

        cursor.execute("""
            INSERT INTO treinos (aluno_id, personal_id, tipo_treino, descricao, dia_semana, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (aluno_id, personal_id, tipo_treino, descricao, dia_semana, data_hoje()))
        conexao.commit()
        conexao.close()

        messagebox.showinfo("Sucesso", "Treino cadastrado com sucesso!")
        janela.destroy()

    tk.Button(janela, text="Salvar Treino", command=salvar_treino, bg="lightgreen", width=15).pack(pady=15)


def abrir_ver_treinos(personal_id_fixo):
    janela = tk.Toplevel(janela_principal)
    janela.title("Treinos de um Aluno")
    janela.geometry("450x520")

    tk.Label(janela, text="TREINOS DE UM ALUNO", font=("Arial", 12, "bold")).pack(pady=10)

    if personal_id_fixo:
        tk.Label(janela, text="Meus alunos:").pack()
    else:
        tk.Label(janela, text="Alunos cadastrados:").pack()

    caixa_alunos = tk.Text(janela, width=50, height=6)
    caixa_alunos.pack(pady=5)

    conexao = conectar()
    cursor = conexao.cursor()
    if personal_id_fixo:
        cursor.execute("SELECT id, nome FROM alunos WHERE personal_id = ?", (personal_id_fixo,))
    else:
        cursor.execute("SELECT id, nome FROM alunos")
    for a in cursor.fetchall():
        caixa_alunos.insert(tk.END, f"{a[0]} - {a[1]}\n")
    conexao.close()

    tk.Label(janela, text="Digite o ID do aluno:").pack()
    entry_aluno_id = tk.Entry(janela, width=10)
    entry_aluno_id.pack()

    caixa_resultado = tk.Text(janela, width=50, height=14)
    caixa_resultado.pack(pady=10)

    def buscar_treinos():
        caixa_resultado.delete("1.0", tk.END)
        aluno_id = entry_aluno_id.get()

        conexao = conectar()
        cursor = conexao.cursor()

        if personal_id_fixo:
            cursor.execute("SELECT personal_id FROM alunos WHERE id = ?", (aluno_id,))
            dono_do_aluno = cursor.fetchone()
            if not dono_do_aluno or dono_do_aluno[0] != personal_id_fixo:
                caixa_resultado.insert(tk.END, "Esse aluno nao e seu.")
                conexao.close()
                return

        cursor.execute("""
            SELECT treinos.tipo_treino, treinos.descricao, treinos.dia_semana, personais.nome
            FROM treinos
            JOIN personais ON treinos.personal_id = personais.id
            WHERE treinos.aluno_id = ?
        """, (aluno_id,))
        resultado = cursor.fetchall()
        conexao.close()

        if len(resultado) == 0:
            caixa_resultado.insert(tk.END, "Esse aluno ainda nao tem treinos cadastrados.")
        else:
            for t in resultado:
                dia = t[2] if t[2] else "Sem dia definido"
                caixa_resultado.insert(
                    tk.END,
                    f"Dia: {dia}\nTipo: {t[0]}\nDescricao: {t[1]}\nFuncionario: {t[3]}\n\n"
                )

    tk.Button(janela, text="Buscar Treinos", command=buscar_treinos, bg="lightyellow", width=15).pack()


# ==========================================================
# AGENDAMENTO DE AULAS
# ==========================================================

def abrir_agendar_aula(personal_id_fixo):
    janela = tk.Toplevel(janela_principal)
    janela.title("Agendar Aula")
    janela.geometry("400x520")

    tk.Label(janela, text="AGENDAR AULA", font=("Arial", 12, "bold")).pack(pady=10)

    if personal_id_fixo:
        tk.Label(janela, text="Meus alunos:").pack()
    else:
        tk.Label(janela, text="Alunos cadastrados:").pack()

    caixa_alunos = tk.Text(janela, width=45, height=8)
    caixa_alunos.pack(pady=5)

    conexao = conectar()
    cursor = conexao.cursor()
    if personal_id_fixo:
        cursor.execute("SELECT id, nome FROM alunos WHERE personal_id = ?", (personal_id_fixo,))
    else:
        cursor.execute("SELECT id, nome FROM alunos")
    for a in cursor.fetchall():
        caixa_alunos.insert(tk.END, f"{a[0]} - {a[1]}\n")
    conexao.close()

    tk.Label(janela, text="Digite o ID do aluno:").pack()
    entry_aluno_id = tk.Entry(janela, width=10)
    entry_aluno_id.pack()

    tk.Label(janela, text="Data da aula (dd/mm/aaaa):").pack(pady=(10, 0))
    entry_data = tk.Entry(janela, width=20)
    entry_data.pack()

    tk.Label(janela, text="Horario (hh:mm):").pack()
    entry_horario = tk.Entry(janela, width=20)
    entry_horario.pack()

    def salvar_agendamento():
        aluno_id = entry_aluno_id.get()

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT personal_id FROM alunos WHERE id = ?", (aluno_id,))
        aluno = cursor.fetchone()

        if not aluno:
            messagebox.showerror("Erro", "Aluno nao encontrado.")
            conexao.close()
            return

        if not aluno[0]:
            messagebox.showerror("Erro", "Esse aluno nao tem funcionario atribuido.")
            conexao.close()
            return

        if personal_id_fixo and aluno[0] != personal_id_fixo:
            messagebox.showerror("Erro", "Esse aluno nao e seu.")
            conexao.close()
            return

        personal_id = aluno[0]

        cursor.execute("""
            INSERT INTO agendamentos (aluno_id, personal_id, data_aula, horario, status)
            VALUES (?, ?, ?, ?, 'AGENDADA')
        """, (aluno_id, personal_id, entry_data.get(), entry_horario.get()))
        conexao.commit()
        conexao.close()

        messagebox.showinfo("Sucesso", "Aula agendada com sucesso!")
        janela.destroy()

    tk.Button(janela, text="Agendar", command=salvar_agendamento, bg="lightgreen", width=15).pack(pady=15)


def abrir_ver_agendamentos(personal_id_fixo):
    janela = tk.Toplevel(janela_principal)
    janela.title("Lista de Agendamentos")
    janela.geometry("480x420")

    tk.Label(janela, text="LISTA DE AGENDAMENTOS", font=("Arial", 12, "bold")).pack(pady=10)

    caixa_texto = tk.Text(janela, width=58, height=18)
    caixa_texto.pack(padx=10, pady=10)

    conexao = conectar()
    cursor = conexao.cursor()
    if personal_id_fixo:
        cursor.execute("""
            SELECT agendamentos.id, alunos.nome, personais.nome, agendamentos.data_aula,
                   agendamentos.horario, agendamentos.status
            FROM agendamentos
            JOIN alunos ON agendamentos.aluno_id = alunos.id
            JOIN personais ON agendamentos.personal_id = personais.id
            WHERE agendamentos.personal_id = ?
            ORDER BY agendamentos.data_aula, agendamentos.horario
        """, (personal_id_fixo,))
    else:
        cursor.execute("""
            SELECT agendamentos.id, alunos.nome, personais.nome, agendamentos.data_aula,
                   agendamentos.horario, agendamentos.status
            FROM agendamentos
            JOIN alunos ON agendamentos.aluno_id = alunos.id
            JOIN personais ON agendamentos.personal_id = personais.id
            ORDER BY agendamentos.data_aula, agendamentos.horario
        """)
    resultado = cursor.fetchall()
    conexao.close()

    if len(resultado) == 0:
        caixa_texto.insert(tk.END, "Nenhuma aula agendada.")
    else:
        for ag in resultado:
            caixa_texto.insert(
                tk.END,
                f"ID: {ag[0]} | Aluno: {ag[1]}\nFuncionario: {ag[2]}\nData: {ag[3]} | Horario: {ag[4]} | Status: {ag[5]}\n\n"
            )


# ==========================================================
# COBRANCA DE MENSALIDADE (TODO DIA 10) - so o Dono acessa
# ==========================================================

def gerar_cobrancas_do_mes():
    hoje = datetime.now()
    mes_referencia = hoje.strftime("%m/%Y")
    vencimento = f"10/{hoje.strftime('%m/%Y')}"

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("SELECT id, nome, valor_mensalidade FROM alunos")
    alunos = cursor.fetchall()

    total_geradas = 0
    mensagem = ""

    for aluno in alunos:
        aluno_id, nome, valor = aluno

        cursor.execute("""
            SELECT id FROM pagamentos WHERE aluno_id = ? AND mes_referencia = ?
        """, (aluno_id, mes_referencia))
        ja_existe = cursor.fetchone()

        if not ja_existe:
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


def verificar_cobranca_automatica():
    """
    Chamada automaticamente ao abrir o sistema (se a academia ja existir).
    Se hoje for dia 10, gera as cobrancas do mes sem precisar o usuario pedir.
    """
    hoje = datetime.now()
    if hoje.day == 10:
        mes_referencia = hoje.strftime("%m/%Y")
        vencimento = f"10/{hoje.strftime('%m/%Y')}"

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, valor_mensalidade FROM alunos")
        alunos = cursor.fetchall()

        for aluno_id, valor in alunos:
            cursor.execute("""
                SELECT id FROM pagamentos WHERE aluno_id = ? AND mes_referencia = ?
            """, (aluno_id, mes_referencia))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO pagamentos (aluno_id, valor, mes_referencia, data_vencimento, status)
                    VALUES (?, ?, ?, ?, 'PENDENTE')
                """, (aluno_id, valor, mes_referencia, vencimento))

        conexao.commit()
        conexao.close()

        messagebox.showinfo("Cobranca Automatica", "Hoje e dia 10! As cobrancas do mes foram geradas automaticamente.")


def abrir_ver_pagamentos():
    janela = tk.Toplevel(janela_principal)
    janela.title("Lista de Pagamentos")
    janela.geometry("480x420")

    tk.Label(janela, text="LISTA DE PAGAMENTOS", font=("Arial", 12, "bold")).pack(pady=10)

    caixa_texto = tk.Text(janela, width=58, height=18)
    caixa_texto.pack(padx=10, pady=10)

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT pagamentos.id, alunos.nome, pagamentos.valor, pagamentos.mes_referencia,
               pagamentos.data_vencimento, pagamentos.status
        FROM pagamentos
        JOIN alunos ON pagamentos.aluno_id = alunos.id
        ORDER BY pagamentos.mes_referencia DESC
    """)
    resultado = cursor.fetchall()
    conexao.close()

    if len(resultado) == 0:
        caixa_texto.insert(tk.END, "Nenhum pagamento registrado ainda.")
    else:
        for p in resultado:
            caixa_texto.insert(
                tk.END,
                f"ID: {p[0]} | Aluno: {p[1]}\nValor: R$ {p[2]:.2f} | Mes: {p[3]}\n"
                f"Vencimento: {p[4]} | Status: {p[5]}\n\n"
            )


def abrir_marcar_pagamento():
    janela = tk.Toplevel(janela_principal)
    janela.title("Marcar Pagamento como Pago")
    janela.geometry("350x200")

    tk.Label(janela, text="MARCAR PAGAMENTO COMO PAGO", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(janela, text="Digite o ID do pagamento:").pack()
    entry_id = tk.Entry(janela, width=15)
    entry_id.pack(pady=5)

    def salvar_pagamento():
        id_pagamento = entry_id.get()

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id FROM pagamentos WHERE id = ?", (id_pagamento,))
        pagamento = cursor.fetchone()

        if not pagamento:
            messagebox.showerror("Erro", "Pagamento nao encontrado.")
        else:
            cursor.execute("""
                UPDATE pagamentos SET status = 'PAGO', data_pagamento = ? WHERE id = ?
            """, (data_hoje(), id_pagamento))
            conexao.commit()
            messagebox.showinfo("Sucesso", "Pagamento marcado como PAGO com sucesso!")
            janela.destroy()

        conexao.close()

    tk.Button(janela, text="Marcar como Pago", command=salvar_pagamento, bg="lightgreen", width=18).pack(pady=15)


# ==========================================================
# INICIO DO PROGRAMA
# ==========================================================

if __name__ == "__main__":
    criar_tabelas()

    if academia_existe():
        verificar_cobranca_automatica()
        tela_login()
    else:
        tela_cadastro_academia()

    janela_principal.mainloop()