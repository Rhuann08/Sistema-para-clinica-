from datetime import datetime
import banco
from prioridades import ordenar_fila

def duracao(inicio, fim):
    return max(0, (datetime.fromisoformat(fim) - datetime.fromisoformat(inicio)).total_seconds()/60)

def media(sid):
    m = banco.consultar("SELECT AVG(tempo_sala) m FROM atendimentos WHERE especialista=?", (sid,))[0]["m"]
    return 30 if m is None else m

def estimar(eid, senha_id):
    fila = ordenar_fila(banco.consultar(
        "SELECT * FROM senhas WHERE especialidade=? AND status='Aguardando'", (eid,)))
    profissionais = banco.consultar("""SELECT s.id, c.nome sala FROM especialistas s
        JOIN consultorios c ON c.id=s.consultorio WHERE s.especialidade=?""", (eid,))
    if not profissionais:
        raise ValueError("Não há especialista disponível.")
    previsao = []
    for p in profissionais:
        m = media(p["id"])
        atual = banco.consultar("SELECT inicio FROM senhas WHERE especialista=? AND status='Em atendimento'", (p["id"],))
        restante = max(0, m-duracao(atual[0]["inicio"], datetime.now().isoformat())) if atual else 0
        previsao.append([restante, p["id"], m, p["sala"]])
    for i, paciente in enumerate(fila):
        p = min(previsao, key=lambda x: (x[0], x[1]))
        if paciente["id"] == senha_id:
            return round(p[0], 1), i, p[3]
        p[0] += p[2]
    raise ValueError("Senha não está aguardando.")
