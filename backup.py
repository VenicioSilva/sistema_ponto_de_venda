import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk
import sqlite3
import qrcode
import re
from PIL import Image, ImageTk

# Conectar ao banco de dados SQLite
conn = sqlite3.connect('supermercado.db')
cursor = conn.cursor()

# Criar tabelas se não existirem
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE,
    descricao TEXT,
    preco REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS transacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendedor TEXT,
    total REAL,
    cpf TEXT,
    forma_pagamento TEXT,
    data TEXT
)
''')

conn.commit()

# Função para validar CPF


def validar_cpf(cpf):
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10 % 11) % 10
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10 % 11) % 10
    return digito1 == int(cpf[9]) and digito2 == int(cpf[10])


# Variáveis globais
total_purchase = 0.0
purchased_products = []
logged_user = None

# Função para cadastro de usuários (apenas para gerentes)


def cadastrar_usuario():
    if not logged_user or logged_user[3] != 'gerente':
        messagebox.showwarning(
            "Acesso Negado", "Apenas gerentes podem cadastrar usuários.")
        return

    username = simpledialog.askstring("Cadastro", "Usuário:")
    password = simpledialog.askstring("Cadastro", "Senha:")
    role = simpledialog.askstring("Cadastro", "Cargo (vendedor/gerente):")

    try:
        cursor.execute("INSERT INTO usuarios (username, password, role) VALUES (?, ?, ?)",
                       (username, password, role))
        conn.commit()
        messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Erro", "Usuário já existe!")

# Função para login de usuários


# Função para login de usuários
def login_usuario():
    global logged_user
    login_window = tk.Toplevel(root)
    login_window.title("Login")

    tk.Label(login_window, text="Usuário:").pack(pady=5)
    username_entry = ttk.Entry(login_window)
    username_entry.pack(pady=5)

    tk.Label(login_window, text="Senha:").pack(pady=5)
    password_entry = ttk.Entry(login_window, show="*")
    password_entry.pack(pady=5)

    # Função para alternar entre mostrar e ocultar a senha
    def toggle_password():
        if password_entry.cget('show') == '*':
            password_entry.config(show='')
            toggle_button.config(text="🙈")  # Ícone de olho fechado
        else:
            password_entry.config(show='*')
            toggle_button.config(text="👁️")  # Ícone de olho aberto

    # Botão de alternância de visibilidade da senha
    toggle_button = ttk.Button(
        login_window, text="👁️", width=3, command=toggle_password)
    toggle_button.pack(pady=5)

    def try_login():
        username = username_entry.get()
        password = password_entry.get()

        cursor.execute(
            "SELECT * FROM usuarios WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()

        if user:
            global logged_user
            logged_user = user
            messagebox.showinfo("Bem-vindo", f"Bem-vindo, {username}!")
            login_window.destroy()
            root.deiconify()
        else:
            messagebox.showerror("Erro", "Credenciais inválidas!")

    ttk.Button(login_window, text="Login", command=try_login).pack(pady=10)
 # Fecha a aplicação se fechar a janela de login
    login_window.protocol("WM_DELETE_WINDOW", root.destroy)

# Função para adicionar produto pelo código


def add_product_by_code():
    global total_purchase
    product_code = product_code_entry.get().strip()

    # Limpar a imagem do QR Code ao adicionar um novo produto
    qr_label.config(image='')
    qr_label.image = None

    cursor.execute("SELECT * FROM produtos WHERE codigo=?", (product_code,))
    product = cursor.fetchone()

    if product:
        description, price = product[2], product[3]
        total_purchase += price
        purchased_products.append((product_code, description, price))
        purchase_list.insert("", "end", values=(
            product_code, description, f"R$ {price:.2f}"))
        total_label.config(text=f"Total da Compra: R$ {total_purchase:.2f}")
        product_code_entry.delete(0, tk.END)
    else:
        messagebox.showerror("Erro", "Código de produto inválido!")


# Função para gerar QR Code para PIX


def gerar_qr_code(total):
    qr = qrcode.make(f"pix://pagamento?valor={total:.2f}")
    qr.save("qrcode.png")
    img = Image.open("qrcode.png")
    img = img.resize((200, 200))
    img_tk = ImageTk.PhotoImage(img)
    qr_label.config(image=img_tk)
    qr_label.image = img_tk

# Função para finalizar compra


def finalizar_compra():
    global total_purchase, purchased_products

    if total_purchase == 0:
        messagebox.showwarning("Aviso", "Nenhum produto adicionado!")
        return

    cpf = ""
    if messagebox.askquestion("CPF na Nota", "Deseja incluir CPF na nota?") == "yes":
        cpf = simpledialog.askstring("CPF", "Digite o CPF:")
        if not validar_cpf(cpf):
            messagebox.showerror("Erro", "CPF inválido!")
            return

    forma_pagamento = simpledialog.askstring(
        "Pagamento", "Forma de pagamento (dinheiro/cartão/pix):")

    # Verifica se a forma de pagamento é Pix e exibe o QR Code
    if forma_pagamento == "pix":
        gerar_qr_code(total_purchase)
        messagebox.showinfo(
            "Pagamento PIX", "Pagamento via PIX realizado com sucesso!")
        resetar_compra()
        return  # Finaliza a função para não continuar abaixo

    # Se o pagamento for em dinheiro, perguntar sobre o troco
    if forma_pagamento == "dinheiro":
        dinheiro_recebido = simpledialog.askfloat(
            "Pagamento em Dinheiro", "Valor recebido (R$):")
        if dinheiro_recebido < total_purchase:
            messagebox.showerror("Erro", "Valor insuficiente!")
            return
        troco = dinheiro_recebido - total_purchase
        messagebox.showinfo("Troco", f"Troco: R$ {troco:.2f}")

    cursor.execute("INSERT INTO transacoes (vendedor, total, cpf, forma_pagamento, data) VALUES (?, ?, ?, ?, datetime('now'))",
                   (logged_user[1], total_purchase, cpf, forma_pagamento))
    conn.commit()

    messagebox.showinfo("Nota Fiscal", f"Compra finalizada!\nTotal: R$ {
                        total_purchase:.2f}\nForma de pagamento: {forma_pagamento}\nCPF: {cpf if cpf else 'Não informado'}")
    resetar_compra()


# Função para resetar compra


def resetar_compra():
    global total_purchase, purchased_products
    total_purchase = 0.0
    purchased_products.clear()
    total_label.config(text="Total da Compra: R$ 0.00")
    purchase_list.delete(*purchase_list.get_children())

    # Limpar a imagem do QR Code
    qr_label.config(image='')
    qr_label.image = None


# Interface gráfica
root = tk.Tk()
root.title("Sistema de Supermercado")
root.withdraw()

login_usuario()

product_code_label = ttk.Label(root, text="Código do Produto:")
product_code_entry = ttk.Entry(root)
add_product_button = ttk.Button(
    root, text="Adicionar Produto", command=add_product_by_code)

purchase_list = ttk.Treeview(root, columns=(
    "code", "description", "price"), show="headings")
purchase_list.heading("code", text="Código")
purchase_list.heading("description", text="Descrição")
purchase_list.heading("price", text="Preço")

total_label = ttk.Label(root, text="Total da Compra: R$ 0.00")
finalizar_button = ttk.Button(
    root, text="Finalizar Compra", command=finalizar_compra)
qr_label = ttk.Label(root)

product_code_label.pack()
product_code_entry.pack()
add_product_button.pack()
purchase_list.pack()
total_label.pack()
finalizar_button.pack()
qr_label.pack()

# Função para adicionar novos produtos ao banco de dados


def adicionar_produto():
    # Verificar se o usuário logado é um gerente
    if logged_user[3] != 'gerente':
        messagebox.showwarning(
            "Permissão Negada", "Apenas gerentes podem adicionar produtos!")
        return

    # Coletar dados do produto
    codigo = simpledialog.askstring(
        "Cadastro de Produto", "Digite o código do produto:")
    descricao = simpledialog.askstring(
        "Cadastro de Produto", "Digite a descrição do produto:")
    preco = simpledialog.askfloat(
        "Cadastro de Produto", "Digite o preço do produto (R$):")

    if not codigo or not descricao or preco is None:
        messagebox.showerror("Erro", "Todos os campos são obrigatórios!")
        return

    try:
        # Inserir o novo produto no banco de dados
        cursor.execute("INSERT INTO produtos (codigo, descricao, preco) VALUES (?, ?, ?)",
                       (codigo, descricao, preco))
        conn.commit()
        messagebox.showinfo("Sucesso", f"Produto '{
                            descricao}' adicionado com sucesso!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Erro", "Código de produto já existe!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao adicionar produto: {str(e)}")


# Adicionar um botão para cadastrar produtos na interface
add_product_btn = ttk.Button(
    root, text="Cadastrar Novo Produto", command=adicionar_produto)
add_product_btn.pack(pady=10)


root.mainloop()
