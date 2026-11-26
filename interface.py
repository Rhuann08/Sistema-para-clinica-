import tkinter as tk
from tkinter import ttk, messagebox

def janela(pai, titulo, tamanho):
    w = tk.Toplevel(pai)
    w.title(titulo)
    w.geometry(tamanho)
    return w

def campo(pai, rotulo, senha=False):
    ttk.Label(pai, text=rotulo).pack(pady=(6,2))
    e = ttk.Entry(pai, width=38, show="*" if senha else "")
    e.pack()
    return e

def combo(pai, rotulo):
    ttk.Label(pai, text=rotulo).pack(pady=(6,2))
    c = ttk.Combobox(pai, width=38, state="readonly")
    c.pack()
    return c

def botao(pai, texto, comando):
    return ttk.Button(pai, text=texto, command=comando)

def id_opcao(texto):
    if not texto:
        raise ValueError("Selecione uma opção.")
    return int(texto.split(" - ",1)[0])

def opcoes(dados):
    return [f"{x['id']} - {x['nome']}" for x in dados]

def login(pai, titulo, autenticar, abrir):
    w = janela(pai,titulo,"350x250")
    ttk.Label(w,text=titulo,font=("Arial",15,"bold")).pack(pady=14)
    u = campo(w,"Usuário")
    s = campo(w,"Senha",True)
    def entrar():
        try:
            dados = autenticar(u.get().strip(),s.get())
            if not dados:
                raise ValueError("Usuário ou senha incorretos.")
            w.destroy()
            abrir(dados)
        except Exception as erro:
            messagebox.showerror("Erro",str(erro),parent=pai)
    botao(w,"Entrar",entrar).pack(pady=15)
