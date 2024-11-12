# Biblioteca padrão do Python para criar interfaces
import tkinter as tk
# Messagebox : Submódulo do tkinter que fornece caixas de diálogo para mostrar mensagens de alerta ou erro ao usuário.
# Simpledialog : Submódulo do tkinter que fornece uma interface para pedir entradas simples do usuário, como caixas de texto.
from tkinter import messagebox, simpledialog
# Submódulo do tkinter que oferece widgets com aparência mais moderna, que são parte da biblioteca Tk themed widgets.
from tkinter import ttk
# Biblioteca para trabalhar com bancos de dados SQLite.
import sqlite3
# Biblioteca para gerar códigos QR.
import qrcode
# Módulo de expressões regulares do Python. Ele fornece funções para procurar padrões dentro de strings, fazer substituições e validar formatos.
import re
# A biblioteca Python Imaging Library (PIL), agora conhecida como Pillow. Ela é usada para abrir, manipular e salvar arquivos de imagem. O Image permite carregar e processar imagens, e o ImageTk converte imagens para que possam ser usadas em widgets do tkinter.
from PIL import Image, ImageTk

# Conectar ao banco de dados SQLite
conn = sqlite3.connect('supermercado.db')
cursor = conn.cursor()
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
total_compra = 0.0
comprado_produtos = []
usuario_logado = None


# Função para adicionar produto pelo código


def add_produto_by_code():
    global total_compra
    code_produto = code_produto_entry.get().strip()

    # Limpar a imagem do QR Code ao adicionar um novo produto
    qr_label.config(image='')
    qr_label.image = None

    cursor.execute("SELECT * FROM produtos WHERE codigo=?", (code_produto,))
    produto = cursor.fetchone()

    if produto:
        descricao, preco = produto[2], produto[3]
        total_compra += preco
        comprado_produtos.append((code_produto, descricao, preco))
        compra_list.insert("", "end", values=(
            code_produto, descricao, f"R$ {preco:.2f}"))
        total_label.config(text=f"Total da Compra: R$ {total_compra:.2f}")
        code_produto_entry.delete(0, tk.END)
    else:
        messagebox.showerror("Erro", "Código de produto inválido!")


# Função para gerar QR Code para PIX


def gerar_qr_code(total):
    qrcode.make(f"pix://pagamento?valor={total:.2f}")
    # Puxa a imagem do qr code.
    img = Image.open("qrcode.png")
    # resolução da imagem
    img = img.resize((200, 200))
    # conversao de imagem.
    img_tk = ImageTk.PhotoImage(img)
    # Atribui a imagem ao widget label no tkinter.
    qr_label.config(image=img_tk)
   # Necessário para evitar que a imagem seja descartada pela coleta de lixo do Python.
    qr_label.image = img_tk

# Função para finalizar compra


def finalizar_compra():
    global total_compra, comprado_produtos

    if total_compra == 0:
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
        gerar_qr_code(total_compra)
        messagebox.showinfo(
            "Pagamento PIX", "Pagamento via PIX realizado com sucesso!")
        resetar_compra()
        return  # Finaliza a função para não continuar abaixo

    # Se o pagamento for em dinheiro, perguntar sobre o troco
    if forma_pagamento == "dinheiro":
        dinheiro_recebido = simpledialog.askfloat(
            "Pagamento em Dinheiro", "Valor recebido (R$):")
        if dinheiro_recebido < total_compra:
            messagebox.showerror("Erro", "Valor insuficiente!")
            return
        troco = dinheiro_recebido - total_compra
        messagebox.showinfo("Troco", f"Troco: R$ {troco:.2f}")

    cursor.execute("INSERT INTO transacoes (vendedor, total, cpf, forma_pagamento, data) VALUES (?, ?, ?, ?, datetime('now'))",
                   (usuario_logado[1], total_compra, cpf, forma_pagamento))
    conn.commit()

    messagebox.showinfo("Nota Fiscal", f"Compra finalizada!\nTotal: R$ {
                        total_compra:.2f}\nForma de pagamento: {forma_pagamento}\nCPF: {cpf if cpf else 'Não informado'}")
    resetar_compra()


# Função para resetar compra


def resetar_compra():
    global total_compra, comprado_produtos
    total_compra = 0.0
    comprado_produtos.clear()
    total_label.config(text="Total da Compra: R$ 0.00")
    compra_list.delete(*compra_list.get_children())

    # Limpar a imagem do QR Code
    qr_label.config(image='')
    qr_label.image = None


# Interface gráfica
root = tk.Tk()
root.title("Sistema de Supermercado")
root.withdraw()


# Função para cadastro de usuários (apenas para gerentes)


# Função para cadastro de usuários (apenas para gerentes)
def cadastrar_usuario():
    if not usuario_logado or usuario_logado[3] != 'gerente':
        messagebox.showwarning(
            "Acesso Negado", "Apenas gerentes podem cadastrar usuários.")
        return

    # Criar janela para cadastro de usuário
    cadastro_window = tk.Toplevel(root)
    cadastro_window.title("Cadastro de Usuário")
    # Tamanho fixo para a janela de cadastro
    cadastro_window.geometry("400x300")
    cadastro_window.lift()  # Traz a janela para frente

    # Função para finalizar o cadastro
    def finalizar_cadastro():
        username = username_entrada.get()
        password = password_entrada.get()
        role = role_entrada.get()

        if username and password and role:
            try:
                cursor.execute("INSERT INTO usuarios (username, password, role) VALUES (?, ?, ?)",
                               (username, password, role))
                conn.commit()
                messagebox.showinfo(
                    "Sucesso", "Usuário cadastrado com sucesso!")
                cadastro_window.destroy()  # Fecha a janela após o cadastro
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Usuário já existe!")
        else:
            messagebox.showerror("Erro", "Todos os campos são obrigatórios!")

    # Labels e campos de entrada para o cadastro de usuário
    tk.Label(cadastro_window, text="Usuário:").pack(pady=5)
    username_entrada = ttk.Entry(cadastro_window)
    username_entrada.pack(pady=5)

    tk.Label(cadastro_window, text="Senha:").pack(pady=5)
    password_entrada = ttk.Entry(cadastro_window, show="*")
    password_entrada.pack(pady=5)

    tk.Label(cadastro_window, text="Cargo (vendedor/gerente):").pack(pady=5)
    role_entrada = ttk.Entry(cadastro_window)
    role_entrada.pack(pady=5)

    # Botão para finalizar o cadastro
    ttk.Button(cadastro_window, text="Cadastrar",
               command=finalizar_cadastro).pack(pady=10)

# Função para criar o botão de cadastro de usuário, que será visível apenas para gerentes


def mostrar_botao_cadastrar_usuario():
    if usuario_logado and usuario_logado[3] == 'gerente':
        cadastrar_usuario_button.pack(pady=10)
    else:
        cadastrar_usuario_button.pack_forget()

# Função de login do usuário


def login_usuario():
    global usuario_logado
    login_window = tk.Toplevel(root)
    login_window.title("Login")
    # Faz com que a janela de login abra maximizada
    login_window.state('zoomed')

    tk.Label(login_window, text="Usuário:").pack(pady=5)
    username_entrada = ttk.Entry(login_window)
    username_entrada.pack(pady=5)

    tk.Label(login_window, text="Senha:").pack(pady=5)
    password_entrada = ttk.Entry(login_window, show="*")
    password_entrada.pack(pady=5)

    # Função para alternar entre mostrar e ocultar a senha
    def toggle_password():
        if password_entrada.cget('show') == '*':
            password_entrada.config(show='')
            toggle_button.config(text="🙈")  # Ícone de olho fechado
        else:
            password_entrada.config(show='*')
            toggle_button.config(text="👁️")  # Ícone de olho aberto

    # Botão de alternância de visibilidade da senha
    toggle_button = ttk.Button(
        login_window, text="👁️", width=3, command=toggle_password)
    toggle_button.pack(pady=5)

    def tentativa_login():
        username = username_entrada.get()
        password = password_entrada.get()

        cursor.execute(
            "SELECT * FROM usuarios WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()

        if user:
            global usuario_logado
            usuario_logado = user
            messagebox.showinfo("Bem-vindo", f"Bem-vindo, {username}!")
            login_window.destroy()
            root.deiconify()  # restaura uma janela que foi minimizada.
            root.state('zoomed')  # Maximizar a janela principal
            # Exibe o botão de cadastro de usuário se for um gerente
            mostrar_botao_cadastrar_usuario()
        else:
            messagebox.showerror("Erro", "Credenciais inválidas!")

    ttk.Button(login_window, text="Login",
               command=tentativa_login).pack(pady=10)
    # Fecha a aplicação se fechar a janela de login
    login_window.protocol("WM_DELETE_WINDOW", root.destroy)


# Adicionar o botão de cadastrar usuário (não será exibido inicialmente)
cadastrar_usuario_button = ttk.Button(
    root, text="Cadastrar Usuário", command=cadastrar_usuario)

# Chama a função de login ao iniciar a aplicação
login_usuario()


code_produto_label = ttk.Label(root, text="Código do Produto:")
code_produto_entry = ttk.Entry(root)
add_produto_button = ttk.Button(
    root, text="Adicionar Produto", command=add_produto_by_code)

compra_list = ttk.Treeview(root, columns=(
    "code", "descricao", "preco"), show="headings")
compra_list.heading("code", text="Código")
compra_list.heading("descricao", text="Descrição")
compra_list.heading("preco", text="Preço")

total_label = ttk.Label(root, text="Total da Compra: R$ 0.00")
finalizar_button = ttk.Button(
    root, text="Finalizar Compra", command=finalizar_compra)
qr_label = ttk.Label(root)

code_produto_label.pack()
code_produto_entry.pack()
add_produto_button.pack()
compra_list.pack()
total_label.pack()
finalizar_button.pack()
qr_label.pack()


# Função para adicionar novos produtos ao banco de dados
def adicionar_produto():
    # Verificar se o usuário logado é um gerente
    if usuario_logado[3] != 'gerente':
        messagebox.showwarning(
            "Permissão Negada", "Apenas gerentes podem adicionar produtos!")
        return

    # Criar janela para cadastro de produto
    produto_window = tk.Toplevel(root)
    produto_window.title("Cadastro de Produto")
    # Tamanho fixo para a janela de cadastro
    produto_window.geometry("300x250")
    produto_window.lift()  # Traz a janela para frente

    # Função para finalizar o cadastro
    def finalizar_cadastro_produto():
        codigo = codigo_entry.get()
        descricao = descricao_entry.get()
        preco = preco_entry.get()

        if codigo and descricao and preco:
            try:
                preco = float(preco)  # Convertendo para float
                cursor.execute("INSERT INTO produtos (codigo, descricao, preco) VALUES (?, ?, ?)",
                               (codigo, descricao, preco))
                conn.commit()
                messagebox.showinfo("Sucesso", f"Produto '{
                                    descricao}' adicionado com sucesso!")
                produto_window.destroy()  # Fecha a janela após o cadastro
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Código de produto já existe!")
            except ValueError:
                messagebox.showerror(
                    "Erro", "Preço deve ser um número válido!")
        else:
            messagebox.showerror("Erro", "Todos os campos são obrigatórios!")

    # Labels e campos de entrada para o cadastro de produto
    tk.Label(produto_window, text="Código do Produto:").pack(pady=5)
    codigo_entry = ttk.Entry(produto_window)
    codigo_entry.pack(pady=5)

    tk.Label(produto_window, text="Descrição:").pack(pady=5)
    descricao_entry = ttk.Entry(produto_window)
    descricao_entry.pack(pady=5)

    tk.Label(produto_window, text="Preço (R$):").pack(pady=5)
    preco_entry = ttk.Entry(produto_window)
    preco_entry.pack(pady=5)

    # Botão para finalizar o cadastro
    ttk.Button(produto_window, text="Cadastrar",
               command=finalizar_cadastro_produto).pack(pady=10)


# Adicionar um botão para cadastrar produtos na interface
add_produto_btn = ttk.Button(
    root, text="Cadastrar Novo Produto", command=adicionar_produto)
add_produto_btn.pack(pady=10)


root.mainloop()
