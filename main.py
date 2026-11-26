import tkinter as tk
from tkinter import ttk
import banco, administrador, paciente, especialista

def iniciar():
    banco.iniciar()
    w = tk.Tk()
    w.title("Sistema de gerenciamento de senhas")
    w.geometry("480x380")
    ttk.Label(w,text="CLÍNICA MÉDICA",font=("Arial",22,"bold")).pack(pady=(28,12))
    ttk.Label(w,text="Selecione o tipo de acesso").pack(pady=10)
    for texto,func in (("Administrador",administrador.login),("Especialista",especialista.login),("Paciente",paciente.painel)):
        ttk.Button(w,text=texto,width=32,command=lambda f=func:f(w)).pack(ipady=7,pady=7)
    ttk.Label(w,text="Estrutura de Dados II - UDF").pack(side="bottom",pady=15)
    w.mainloop()

if __name__ == "__main__":
    iniciar()
