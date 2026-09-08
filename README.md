# 🏋️‍♂️ Sistema de Gestão de Academia

Sistema desktop simples para gerenciar uma academia: cadastro de personais e alunos, atribuição de personal, definição de treinos, agendamento de aulas e cobrança automática de mensalidade todo dia 10.

Feito **100% com bibliotecas padrão do Python** (Tkinter + SQLite) — não precisa instalar nada além do próprio Python.

---

## 📸 Sobre o projeto

O sistema possui duas versões:

| Arquivo | Descrição |
|---|---|
| `academia.py` | Versão em **linha de comando** (terminal), com menu numerado |
| `academia_gui.py` | Versão com **interface gráfica** (janelas), usando Tkinter |

Ambas usam o **mesmo banco de dados** (`academia.db`), então você pode alternar entre elas sem perder nenhum dado.

---

## ✨ Funcionalidades

- 👤 Cadastro e listagem de **Personais Trainers**
- 🙋 Cadastro e listagem de **Alunos**
- 🔗 Atribuição de um aluno a um personal
- 💪 Definição e visualização de **treinos** por aluno
- 📅 Agendamento e visualização de **aulas**
- 💰 Geração automática de **cobranças de mensalidade** todo dia 10
- ✅ Marcação de pagamentos como **pagos**

---

## 🧰 Requisitos

- **Python 3.8** ou superior
- Nenhuma biblioteca externa é necessária — o projeto usa apenas:
  - [`sqlite3`](https://docs.python.org/3/library/sqlite3.html) (banco de dados)
  - [`tkinter`](https://docs.python.org/3/library/tkinter.html) (interface gráfica)
  - [`datetime`](https://docs.python.org/3/library/datetime.html) (datas)

> 💡 O Tkinter já vem instalado por padrão na maioria das instalações do Python no Windows e macOS. No Linux, caso não esteja disponível, instale com:
> ```bash
> sudo apt-get install python3-tk
> ```

---

## ▶️ Como executar

### Interface gráfica (recomendado)

```bash
python academia_gui.py
```

### Versão em linha de comando

```bash
python academia.py
```

Ao rodar pela primeira vez, o arquivo `academia.db` será criado automaticamente na mesma pasta, junto com todas as tabelas necessárias.

---

## 🖱️ Como usar

1. Cadastre pelo menos um **Personal Trainer**.
2. Cadastre um **Aluno**.
3. Use a opção **"Atribuir Aluno a um Personal"** para vincular os dois.
4. Com o vínculo feito, você já pode:
   - Definir treinos para o aluno
   - Agendar aulas
5. As **cobranças de mensalidade** são geradas automaticamente todo dia 10 (ao abrir o sistema nessa data), ou manualmente pela opção **"Gerar Cobranças do Mês"**.

---

## 🗄️ Estrutura do banco de dados

O sistema cria automaticamente 5 tabelas no `academia.db`:

- **personais** — dados dos personal trainers (nome, CPF, CREF, especialidade...)
- **alunos** — dados dos alunos, vinculados a um personal
- **treinos** — treinos cadastrados por aluno
- **agendamentos** — aulas marcadas entre aluno e personal
- **pagamentos** — mensalidades geradas mês a mês, com status `PENDENTE` ou `PAGO`

---

## 📁 Estrutura de arquivos

```
📦 sistema-academia
 ┣ 📜 academia.py         → versão em linha de comando
 ┣ 📜 academia.db         → banco de dados (criado automaticamente)
 ┗ 📜 README.md           → este arquivo
```

---

## ⚠️ Observações

- Não há validação de formato de CPF, telefone ou datas — os campos aceitam texto livre.
- O CPF é único: não é possível cadastrar dois alunos (ou dois personais) com o mesmo CPF.
- Este é um projeto de estudo/aprendizado, sem foco em segurança, autenticação ou uso em produção.
