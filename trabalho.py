"""
SISTEMA DE GESTAO DE ACADEMIA - COM INTERFACE GRAFICA (TKINTER)

Cadastro de Personais e Alunos, atribuicao de personal, definicao de treinos,
agendamento de aulas e cobranca de mensalidade todo dia 10.
"""

import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

NOME_BANCO = "academia.db"


# ==========================================================
# CONEXAO E CRIACAO DO BANCO DE DADOS
# ==========================================================

def conectar():
    conexao = sqlite3.connect(NOME_BANCO)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE,
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


def data_hoje():
    return datetime.now().strftime("%d/%m/%Y")


# ==========================================================
# JANELA PRINCIPAL
# ==========================================================

janela_principal = tk.Tk()
janela_principal.title("Sistema de Gestao de Academia")
janela_principal.geometry("420x680")
janela_principal.configure(bg="#333333")

label_titulo = tk.Label(
    janela_principal,
    text="ACADEMIA DEBUGGERS",
    font=("Arial", 22, "bold"),
    bg="#333333",
    fg="white"
)
label_titulo.pack(pady=15)



#==========================================================
    # Validação para números
#==========================================================

def apenas_numeros(valor):
     return valor.isdigit() or valor == ""



#==========================================================
    # Formatação CPF
#==========================================================
def formatar_cpf(event):
    cpf = event.widget.get()

    cpf = ''.join(filter(str.isdigit, cpf))

    cpf = cpf[:11]

    if len(cpf) > 9:
        cpf = cpf[:3] + "." + cpf[3:6] + "." + cpf[6:9] + "-" + cpf[9:]
    elif len(cpf) > 6:
        cpf = cpf[:3] + "." + cpf[3:6] + "." + cpf[6:]
    elif len(cpf) > 3:
        cpf = cpf[:3] + "." + cpf[3:]

    event.widget.delete(0, tk.END)
    event.widget.insert(0, cpf)


#==========================================================
    # Formatação Data de nascimento
#==========================================================



def formatar_data(event):
    data = event.widget.get()

    data = ''.join(filter(str.isdigit, data))

    data = data[:8]

    if len(data) > 4:
        data = data[:2] + "/" + data[2:4] + "/" + data[4:]
    elif len(data) > 2:
        data = data[:2] + "/" + data[2:]

    event.widget.delete(0, tk.END)
    event.widget.insert(0, data)

# ==========================================================
# CADASTRO DE PERSONAL
# ==========================================================

def abrir_cadastro_personal():
    janela = tk.Toplevel(janela_principal)
    janela.title("Cadastrar Personal")
    janela.geometry("350x520")
    validacao = janela.register(apenas_numeros)

    tk.Label(janela, text="CADASTRO DE PERSONAL TRAINER", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(janela, text="Nome completo:").pack()
    entry_nome = tk.Entry(janela, width=35)
    entry_nome.pack()

    tk.Label(janela, text="CPF:").pack()

    entry_cpf = tk.Entry(
    janela,
    width=35,
    )
    entry_cpf.bind("<KeyRelease>", formatar_cpf)
    entry_cpf.pack()

    tk.Label(janela, text="Data de nascimento (dd/mm/aaaa):").pack()
    entry_nasc = tk.Entry(janela, width=35)
    entry_nasc.bind("<KeyRelease>", formatar_data)
    entry_nasc.pack()

    tk.Label(janela, text="Telefone:").pack()

    entry_tel = tk.Entry(
    janela,
    width=35,
    validate="key",
    validatecommand=(validacao, "%P")
    )
    entry_tel.pack()
    
    tk.Label(janela, text="Email:").pack()
    entry_email = tk.Entry(janela, width=35)
    entry_email.pack()

    tk.Label(janela, text="Endereco:").pack()
    entry_end = tk.Entry(janela, width=35)
    entry_end.pack()

    tk.Label(janela, text="Numero do CREF:").pack()

    entry_cref = tk.Entry(
    janela,
    width=35,
    validate="key",
    validatecommand=(validacao, "%P")
    )
    entry_cref.pack()

    tk.Label(janela, text="Especialidade:").pack()
    entry_esp = tk.Entry(janela, width=35)
    entry_esp.pack()

    def salvar_personal():
        nome = entry_nome.get()
        cpf = entry_cpf.get()

        if nome == "" or cpf == "":
            messagebox.showerror("Erro", "Nome e CPF sao obrigatorios.")
            return

        conexao = conectar()
        cursor = conexao.cursor()
        try:
            cursor.execute("""
                INSERT INTO personais
                (nome, cpf, data_nascimento, telefone, email, endereco, cref, especialidade, data_cadastro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (nome, cpf, entry_nasc.get(), entry_tel.get(), entry_email.get(),
                  entry_end.get(), entry_cref.get(), entry_esp.get(), data_hoje()))
            conexao.commit()
            messagebox.showinfo("Sucesso", "Personal cadastrado com sucesso! ID: " + str(cursor.lastrowid))
            janela.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Ja existe um personal cadastrado com esse CPF.")
        finally:
            conexao.close()

    tk.Button(janela, text="Salvar", command=salvar_personal, bg="lightgreen", width=15).pack(pady=15)


def abrir_lista_personais():
    janela = tk.Toplevel(janela_principal)
    janela.title("Lista de Personais")
    janela.geometry("450x400")

    tk.Label(janela, text="LISTA DE PERSONAIS", font=("Arial", 12, "bold")).pack(pady=10)

    caixa_texto = tk.Text(janela, width=55, height=18)
    caixa_texto.pack(padx=10, pady=10)

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome, cpf, telefone, especialidade FROM personais")
    resultado = cursor.fetchall()
    conexao.close()

    if len(resultado) == 0:
        caixa_texto.insert(tk.END, "Nenhum personal cadastrado.")
    else:
        for p in resultado:
            caixa_texto.insert(
                tk.END,
                f"ID: {p[0]} | Nome: {p[1]}\nCPF: {p[2]} | Tel: {p[3]}\nEspecialidade: {p[4]}\n\n"
            )


# ==========================================================
# CADASTRO DE ALUNO
# ==========================================================

def abrir_cadastro_aluno():
    janela = tk.Toplevel(janela_principal)
    janela.title("Cadastrar Aluno")
    janela.geometry("350x600")
    validacao = janela.register(apenas_numeros)

    tk.Label(janela, text="CADASTRO DE ALUNO", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(janela, text="Nome completo:").pack()
    entry_nome = tk.Entry(janela, width=35)
    entry_nome.pack()

    tk.Label(janela, text="CPF:").pack()
    entry_cpf = tk.Entry(janela, width=35)
    entry_cpf.bind("<KeyRelease>", formatar_cpf)
    entry_cpf.pack()

    tk.Label(janela, text="Data de nascimento (dd/mm/aaaa):").pack()
    entry_nasc = tk.Entry(janela, width=35)
    entry_nasc.bind("<KeyRelease>", formatar_data)
    entry_nasc.pack()

    tk.Label(janela, text="Telefone:").pack()
    entry_tel = tk.Entry(janela, width=35,
    validate="key",
    validatecommand=(validacao, "%P"))
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
    entry_valor = tk.Entry(janela, width=35,
    validate="key",
    validatecommand=(validacao, "%P"))
    entry_valor.pack()

    def salvar_aluno():
        nome = entry_nome.get()
        cpf = entry_cpf.get()

        if nome == "" or cpf == "":
            messagebox.showerror("Erro", "Nome e CPF sao obrigatorios.")
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
                (nome, cpf, data_nascimento, telefone, email, endereco, objetivo, plano,
                 valor_mensalidade, personal_id, data_cadastro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
            """, (nome, cpf, entry_nasc.get(), entry_tel.get(), entry_email.get(),
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
# ATRIBUIR ALUNO A UM PERSONAL
# ==========================================================

def abrir_atribuir_personal():
    janela = tk.Toplevel(janela_principal)
    janela.title("Atribuir Aluno a um Personal")
    janela.geometry("400x550")

    tk.Label(janela, text="ATRIBUIR ALUNO A UM PERSONAL", font=("Arial", 12, "bold")).pack(pady=10)

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

    tk.Label(janela, text="Personais cadastrados:").pack(pady=(10, 0))
    caixa_personais = tk.Text(janela, width=45, height=8)
    caixa_personais.pack(pady=5)

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome FROM personais")
    for p in cursor.fetchall():
        caixa_personais.insert(tk.END, f"{p[0]} - {p[1]}\n")
    conexao.close()

    tk.Label(janela, text="Digite o ID do personal:").pack()
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
            messagebox.showerror("Erro", "Personal nao encontrado.")
        else:
            cursor.execute("UPDATE alunos SET personal_id = ? WHERE id = ?", (personal_id, aluno_id))
            conexao.commit()
            messagebox.showinfo("Sucesso", "Aluno atribuido ao personal com sucesso!")
            janela.destroy()

        conexao.close()

    tk.Button(janela, text="Atribuir", command=salvar_atribuicao, bg="lightgreen", width=15).pack(pady=15)


# ==========================================================
# DEFINIR TREINO DO ALUNO
# ==========================================================

def abrir_definir_treino():
    janela = tk.Toplevel(janela_principal)
    janela.title("Definir Treino do Aluno")
    janela.geometry("400x550")

    tk.Label(janela, text="DEFINIR TREINO DO ALUNO", font=("Arial", 12, "bold")).pack(pady=10)

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

    tk.Label(janela, text="Tipo de treino (ex: Musculacao, Cardio, Funcional):").pack(pady=(10, 0))
    entry_tipo = tk.Entry(janela, width=35)
    entry_tipo.pack()

    tk.Label(janela, text="Descricao do treino:").pack()
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
            messagebox.showerror("Erro", "Esse aluno ainda nao tem um personal atribuido. Atribua um personal primeiro.")
            conexao.close()
            return

        personal_id = aluno[1]
        tipo_treino = entry_tipo.get()
        descricao = texto_descricao.get("1.0", tk.END).strip()

        cursor.execute("""
            INSERT INTO treinos (aluno_id, personal_id, tipo_treino, descricao, data_criacao)
            VALUES (?, ?, ?, ?, ?)
        """, (aluno_id, personal_id, tipo_treino, descricao, data_hoje()))
        conexao.commit()
        conexao.close()

        messagebox.showinfo("Sucesso", "Treino cadastrado com sucesso!")
        janela.destroy()

    tk.Button(janela, text="Salvar Treino", command=salvar_treino, bg="lightgreen", width=15).pack(pady=15)


def abrir_ver_treinos():
    janela = tk.Toplevel(janela_principal)
    janela.title("Treinos de um Aluno")
    janela.geometry("450x500")

    tk.Label(janela, text="TREINOS DE UM ALUNO", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(janela, text="Alunos cadastrados:").pack()
    caixa_alunos = tk.Text(janela, width=50, height=6)
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

    caixa_resultado = tk.Text(janela, width=50, height=14)
    caixa_resultado.pack(pady=10)

    def buscar_treinos():
        caixa_resultado.delete("1.0", tk.END)
        aluno_id = entry_aluno_id.get()

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT treinos.tipo_treino, treinos.descricao, treinos.data_criacao, personais.nome
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
                caixa_resultado.insert(
                    tk.END,
                    f"Tipo: {t[0]}\nDescricao: {t[1]}\nData: {t[2]}\nPersonal: {t[3]}\n\n"
                )

    tk.Button(janela, text="Buscar Treinos", command=buscar_treinos, bg="lightyellow", width=15).pack()


# ==========================================================
# AGENDAMENTO DE AULAS
# ==========================================================

def abrir_agendar_aula():
    janela = tk.Toplevel(janela_principal)
    janela.title("Agendar Aula")
    janela.geometry("400x500")

    tk.Label(janela, text="AGENDAR AULA", font=("Arial", 12, "bold")).pack(pady=10)

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
            messagebox.showerror("Erro", "Esse aluno nao tem personal atribuido. Atribua um personal antes de agendar.")
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


def abrir_ver_agendamentos():
    janela = tk.Toplevel(janela_principal)
    janela.title("Lista de Agendamentos")
    janela.geometry("480x420")

    tk.Label(janela, text="LISTA DE AGENDAMENTOS", font=("Arial", 12, "bold")).pack(pady=10)

    caixa_texto = tk.Text(janela, width=58, height=18)
    caixa_texto.pack(padx=10, pady=10)

    conexao = conectar()
    cursor = conexao.cursor()
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
                f"ID: {ag[0]} | Aluno: {ag[1]}\nPersonal: {ag[2]}\nData: {ag[3]} | Horario: {ag[4]} | Status: {ag[5]}\n\n"
            )


# ==========================================================
# COBRANCA DE MENSALIDADE (TODO DIA 10)
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
    Chamada automaticamente ao abrir o sistema.
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
# BOTOES DO MENU PRINCIPAL
# ==========================================================

tk.Button(janela_principal, text="1 - Cadastrar Personal", width=30, command=abrir_cadastro_personal).pack(pady=3)
tk.Button(janela_principal, text="2 - Listar Personais", width=30, command=abrir_lista_personais).pack(pady=3)
tk.Button(janela_principal, text="3 - Cadastrar Aluno", width=30, command=abrir_cadastro_aluno).pack(pady=3)
tk.Button(janela_principal, text="4 - Listar Alunos", width=30, command=abrir_lista_alunos).pack(pady=3)
tk.Button(janela_principal, text="5 - Atribuir Aluno a um Personal", width=30, command=abrir_atribuir_personal).pack(pady=3)
tk.Button(janela_principal, text="6 - Definir Treino do Aluno", width=30, command=abrir_definir_treino).pack(pady=3)
tk.Button(janela_principal, text="7 - Ver Treinos de um Aluno", width=30, command=abrir_ver_treinos).pack(pady=3)
tk.Button(janela_principal, text="8 - Agendar Aula", width=30, command=abrir_agendar_aula).pack(pady=3)
tk.Button(janela_principal, text="9 - Ver Agendamentos", width=30, command=abrir_ver_agendamentos).pack(pady=3)
tk.Button(janela_principal, text="10 - Gerar Cobrancas do Mes", width=30, command=gerar_cobrancas_do_mes).pack(pady=3)
tk.Button(janela_principal, text="11 - Ver Pagamentos", width=30, command=abrir_ver_pagamentos).pack(pady=3)
tk.Button(janela_principal, text="12 - Marcar Pagamento como Pago", width=30, command=abrir_marcar_pagamento).pack(pady=3)

tk.Button(
    janela_principal,
    text="Sair",
    width=30,
    bg="salmon",
    command=janela_principal.destroy
).pack(pady=15)


# ==========================================================
# INICIO DO PROGRAMA
# ==========================================================

if __name__ == "__main__":
    criar_tabelas()
    verificar_cobranca_automatica()
    janela_principal.mainloop()
