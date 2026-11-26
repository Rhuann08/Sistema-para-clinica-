from datetime import datetime
import banco
from prioridades import PRIORIDADES, ordenar_fila
from tempo_espera import duracao

def emitir(eid, categoria):
    if categoria not in PRIORIDADES:
        raise ValueError("Categoria inválida.")
    prefixo = "N" if categoria == "Normal" else "P"
    with banco.conectar() as con:
        con.execute("BEGIN IMMEDIATE")
        if not con.execute("SELECT id FROM especialistas WHERE especialidade=?", (eid,)).fetchone():
            raise ValueError("Não há especialista cadastrado nessa especialidade.")
        ultimo = con.execute("""SELECT numero FROM senhas WHERE especialidade=?
            AND numero LIKE ? ORDER BY id DESC LIMIT 1""", (eid,prefixo+"%")).fetchone()
        n = int(ultimo[0][1:])+1 if ultimo else 1
        numero = f"{prefixo}{n:03d}"
        cur = con.execute("""INSERT INTO senhas(numero,especialidade,categoria,prioridade,chegada)
            VALUES (?,?,?,?,?)""", (numero,eid,categoria,PRIORIDADES[categoria],datetime.now().isoformat()))
        return cur.lastrowid, numero

def chamar(sid):
    with banco.conectar() as con:
        con.execute("BEGIN IMMEDIATE")
        esp = con.execute("SELECT especialidade FROM especialistas WHERE id=?", (sid,)).fetchone()
        if not esp:
            raise ValueError("Especialista não cadastrado.")
        if con.execute("SELECT 1 FROM senhas WHERE especialista=? AND status='Em atendimento'", (sid,)).fetchone():
            raise ValueError("Finalize o atendimento atual primeiro.")
        fila = ordenar_fila(con.execute("SELECT * FROM senhas WHERE especialidade=? AND status='Aguardando'", (esp[0],)).fetchall())
        if not fila:
            raise ValueError("Fila vazia.")
        p = fila[0]
        con.execute("UPDATE senhas SET especialista=?, inicio=?, status='Em atendimento' WHERE id=?",
                    (sid, datetime.now().isoformat(), p["id"]))
        return p

def finalizar(sid):
    with banco.conectar() as con:
        con.execute("BEGIN IMMEDIATE")
        p = con.execute("""SELECT q.*, c.nome sala FROM senhas q
            JOIN especialistas s ON s.id=q.especialista JOIN consultorios c ON c.id=s.consultorio
            WHERE q.especialista=? AND q.status='Em atendimento'""", (sid,)).fetchone()
        if not p:
            raise ValueError("Não existe atendimento em andamento.")
        fim = datetime.now().isoformat()
        minutos = duracao(p["inicio"], fim)
        con.execute("INSERT INTO atendimentos VALUES (?,?,?,?,?)", (sid,p["sala"],p["inicio"],fim,minutos))
        con.execute("UPDATE senhas SET status='Atendido', fim=? WHERE id=?", (fim,p["id"]))
        return p["numero"], minutos
