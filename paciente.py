import tkinter as tk
from tkinter import ttk, messagebox
import banco
from prioridades import PRIORIDADES
from atendimentos import emitir
from tempo_espera import estimar
from interface import janela, campo, combo, botao, opcoes, id_opcao

def painel(pai):
    w = janela(pai,"Paciente","600x660")
    ttk.Label(w,text="EMISSÃO DE SENHAS",font=("Arial",18,"bold")).pack(pady=12)
    esp = combo(w,"Especialidade")
    tipo = tk.StringVar(master=w,value="Normal")
    for texto in ("Normal","Prioritária"):
        ttk.Radiobutton(w,text=texto,variable=tipo,value=texto).pack(pady=3)
    cat = combo(w,"Categoria de prioridade")
    cat["values"] = [x for x in PRIORIDADES if x!="Normal"]
    def mudar(*args):
        cat.set("")
        cat.configure(state="readonly" if tipo.get()=="Prioritária" else "disabled")
    tipo.trace_add("write",mudar)
    mudar()
    resultado = ttk.Label(w,text="",justify="center",wraplength=540,font=("Arial",12))
    def mostrar():
        try:
            eid = id_opcao(esp.get())
            categoria = "Normal" if tipo.get()=="Normal" else cat.get()
            sid, numero = emitir(eid,categoria)
            numero_c.delete(0,tk.END)
            numero_c.insert(0,numero)
            esp_c.set(esp.get())
            atualizar_senha()
        except Exception as erro:
            messagebox.showerror("Erro",str(erro),parent=w)
    botao(w,"Gerar senha",mostrar).pack(pady=12)
    resultado.pack(pady=8)
    ttk.Separator(w).pack(fill="x",padx=25,pady=10)
    numero_c = campo(w,"Consultar número da senha")
    esp_c = combo(w,"Especialidade da senha")
    def atualizar_senha():
        try:
            eid = id_opcao(esp_c.get())
            dados = banco.consultar("""SELECT q.*,e.nome esp,c.nome sala FROM senhas q
                JOIN especialidades e ON e.id=q.especialidade
                LEFT JOIN especialistas s ON s.id=q.especialista
                LEFT JOIN consultorios c ON c.id=s.consultorio
                WHERE q.numero=? AND q.especialidade=?""",(numero_c.get().strip().upper(),eid))
            if not dados:
                raise ValueError("Senha não encontrada.")
            x = dados[0]
            texto = f"Senha: {x['numero']} | {x['esp']}\n{x['categoria']} | {x['status']}"
            if x["status"] == "Aguardando":
                t,n,sala = estimar(eid,x["id"])
                texto += f"\nConsultório previsto: {sala}\nPacientes à frente: {n}\nEspera estimada: {t:g} minutos"
            else:
                texto += f"\nConsultório: {x['sala']}"
            resultado.configure(text=texto)
        except Exception as erro:
            messagebox.showwarning("Consulta",str(erro),parent=w)
    botao(w,"Consultar / atualizar",atualizar_senha).pack(pady=10)
    def carregar():
        valores = opcoes(banco.consultar("SELECT * FROM especialidades ORDER BY nome"))
        for cb in (esp,esp_c):
            cb["values"] = valores
            if cb.get() not in valores:
                cb.set("")
    botao(w,"Atualizar especialidades",carregar).pack()
    carregar()
