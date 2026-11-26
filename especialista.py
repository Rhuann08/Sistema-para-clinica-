import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import banco
from atendimentos import chamar, finalizar
from prioridades import ordenar_fila
from tempo_espera import media, duracao
from interface import janela, botao, login as tela_login

def login(pai):
    def autenticar(u,s):
        dados = banco.consultar("""SELECT s.*,e.nome esp,c.nome sala FROM especialistas s
            JOIN especialidades e ON e.id=s.especialidade JOIN consultorios c ON c.id=s.consultorio
            WHERE s.usuario=? AND s.senha=?""",(u,s))
        return dados[0] if dados else None
    tela_login(pai,"Login do especialista",autenticar,lambda x: painel(pai,x))

def painel(pai, especialista):
    w = janela(pai,"Especialista","900x680")
    sid,eid = especialista["id"],especialista["especialidade"]
    ttk.Label(w,text=f"{especialista['nome']} | {especialista['esp']} | {especialista['sala']}",font=("Arial",16,"bold")).pack(pady=10)
    ultima = ttk.Label(w,text="",font=("Arial",12,"bold"))
    ultima.pack(pady=5)
    info = ttk.Label(w,text="")
    info.pack()
    def tabela(titulo,colunas,altura):
        ttk.Label(w,text=titulo,font=("Arial",12,"bold")).pack(pady=8)
        t = ttk.Treeview(w,columns=colunas,show="headings",height=altura)
        for col in colunas:
            t.heading(col,text=col)
            t.column(col,width=100 if col!="Categoria" else 300,anchor="center")
        t.pack(fill="x",padx=12)
        return t
    fila = tabela("Fila de espera",("Senha","Categoria","Prioridade","Chegada"),8)
    historico = tabela("Histórico",("Senha","Categoria","Situação","Minutos"),7)
    def atualizar():
        for t in (fila,historico):
            for item in t.get_children():
                t.delete(item)
        pacientes = ordenar_fila(banco.consultar("SELECT * FROM senhas WHERE especialidade=? AND status='Aguardando'",(eid,)))
        for x in pacientes:
            fila.insert("",tk.END,values=(x["numero"],x["categoria"],x["prioridade"],datetime.fromisoformat(x["chegada"]).strftime("%H:%M:%S")))
        dados = banco.consultar("SELECT * FROM senhas WHERE especialista=? ORDER BY inicio DESC",(sid,))
        if dados:
            x = dados[0]
            ultima.configure(text=f"Última senha: {x['numero']} | {x['categoria']} | {x['status']}")
        else:
            ultima.configure(text="Nenhuma senha chamada.")
        info.configure(text=f"Aguardando: {len(pacientes)} | Média: {media(sid):.1f} minutos")
        for x in dados:
            historico.insert("",tk.END,values=(x["numero"],x["categoria"],x["status"],f"{duracao(x['inicio'],x['fim']):.2f}" if x["fim"] else "-"))
    def proximo():
        try:
            x = chamar(sid)
            atualizar()
            messagebox.showinfo("Senha chamada",f"{x['numero']} | {especialista['esp']}\n{x['categoria']} | {especialista['sala']}",parent=w)
        except Exception as erro:
            messagebox.showwarning("Atendimento",str(erro),parent=w)
    def terminar():
        try:
            n,m = finalizar(sid)
            atualizar()
            messagebox.showinfo("Finalizado",f"{n} | {m:.2f} minutos",parent=w)
        except Exception as erro:
            messagebox.showwarning("Atendimento",str(erro),parent=w)
    b = ttk.Frame(w)
    b.pack(pady=12)
    for texto,func in (("Chamar próximo",proximo),("Finalizar atendimento",terminar),("Atualizar fila",atualizar)):
        botao(b,texto,func).pack(side="left",padx=5)
    # O callback é cancelado antes de fechar a janela.
    tarefa = None
    def automatico():
        nonlocal tarefa
        atualizar()
        tarefa = w.after(2000,automatico)
    def fechar():
        if tarefa is not None:
            w.after_cancel(tarefa)
        w.destroy()
    w.protocol("WM_DELETE_WINDOW",fechar)
    automatico()
