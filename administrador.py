import tkinter as tk
from tkinter import ttk, messagebox
import banco, cadastros
from interface import janela, campo, combo, botao, id_opcao, opcoes, login as tela_login

def login(pai):
    tela_login(pai,"Login do administrador",lambda u,s: u=="admin" and s=="admin123",lambda _: painel(pai))

def painel(pai):
    w = janela(pai,"Administrador","850x730")
    abas = ttk.Notebook(w)
    abas.pack(fill="both",expand=True,padx=12,pady=12)
    c,e,s = [ttk.Frame(abas) for _ in range(3)]
    for aba,nome in ((c,"Consultórios"),(e,"Especialidades"),(s,"Especialistas")):
        abas.add(aba,text=nome)

    def operacao(funcao, limpar=()):
        try:
            funcao()
            for caixa in limpar:   # esvazia os campos só quando deu certo
                caixa.delete(0,tk.END)
            atualizar()
            messagebox.showinfo("Cadastro","Operação realizada.",parent=w)
        except Exception as erro:
            messagebox.showerror("Erro",cadastros.mensagem_erro(erro),parent=w)

    def lista(pai, altura):
        l = tk.Listbox(pai,width=85,height=altura,exportselection=False)
        l.pack(pady=8)
        return l

    def selecionado(l):
        if not l.curselection():
            raise ValueError("Selecione um registro.")
        return id_opcao(l.get(l.curselection()[0]))

    nc = campo(c,"Nome do consultório")
    lc = lista(c,12)
    botao(c,"Cadastrar",lambda: operacao(lambda: cadastros.cadastrar_nome("consultorios",nc.get()),(nc,))).pack(pady=4)
    botao(c,"Remover",lambda: operacao(lambda: banco.executar("DELETE FROM consultorios WHERE id=?",(selecionado(lc),)))).pack()

    ne = campo(e,"Nome da especialidade")
    le = lista(e,5)
    botao(e,"Cadastrar",lambda: operacao(lambda: cadastros.cadastrar_nome("especialidades",ne.get()),(ne,))).pack()
    botao(e,"Remover",lambda: operacao(lambda: banco.executar("DELETE FROM especialidades WHERE id=?",(selecionado(le),)))).pack(pady=4)
    cc = combo(e,"Consultório")
    ce = combo(e,"Especialidade")
    botao(e,"Vincular (máximo 3)",lambda: operacao(lambda: cadastros.vincular(id_opcao(cc.get()),id_opcao(ce.get())))).pack(pady=4)
    botao(e,"Desvincular",lambda: operacao(lambda: banco.executar("DELETE FROM vinculos WHERE consultorio=? AND especialidade=?",(id_opcao(cc.get()),id_opcao(ce.get()))))).pack()
    lv = lista(e,5)

    ns = campo(s,"Nome do especialista")
    us = campo(s,"Usuário")
    ss = campo(s,"Senha",True)
    cs = combo(s,"Consultório")
    es = combo(s,"Especialidade")
    ls = lista(s,9)

    def mudar(event=None):
        es.set("")
        es["values"] = opcoes(banco.consultar("""SELECT e.* FROM especialidades e
            JOIN vinculos v ON v.especialidade=e.id WHERE v.consultorio=?""",(id_opcao(cs.get()),))) if cs.get() else []

    cs.bind("<<ComboboxSelected>>",mudar)
    botao(s,"Cadastrar especialista",lambda: operacao(lambda: cadastros.cadastrar_especialista(ns.get(),us.get(),ss.get(),id_opcao(cs.get()),id_opcao(es.get())),(ns,us,ss))).pack(pady=4)
    botao(s,"Remover especialista",lambda: operacao(lambda: cadastros.remover_especialista(selecionado(ls)))).pack()

    def preencher(l, valores):
        l.delete(0,tk.END)
        for v in valores:
            l.insert(tk.END,v)

    def atualizar():
        consultorios = opcoes(banco.consultar("SELECT * FROM consultorios ORDER BY nome"))
        especialidades = opcoes(banco.consultar("SELECT * FROM especialidades ORDER BY nome"))
        preencher(lc,consultorios)
        preencher(le,especialidades)
        for cb, valores in ((cc,consultorios),(cs,consultorios),(ce,especialidades)):
            cb["values"] = valores
            if cb.get() not in valores:
                cb.set("")
        mudar()
        vinculos = banco.consultar("""SELECT c.nome sala,e.nome esp FROM vinculos v
            JOIN consultorios c ON c.id=v.consultorio JOIN especialidades e ON e.id=v.especialidade""")
        preencher(lv,[f"{x['sala']} | {x['esp']}" for x in vinculos])
        especialistas = banco.consultar("""SELECT s.id,s.nome,s.usuario,c.nome sala,e.nome esp FROM especialistas s
            JOIN consultorios c ON c.id=s.consultorio JOIN especialidades e ON e.id=s.especialidade""")
        preencher(ls,[f"{x['id']} - {x['nome']} | {x['usuario']} | {x['sala']} | {x['esp']}" for x in especialistas])
    atualizar()
