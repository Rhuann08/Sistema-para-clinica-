import sqlite3
import banco

def cadastrar_nome(tabela, nome):
    if tabela not in ("consultorios", "especialidades"):
        raise ValueError("Cadastro inválido.")
    if not nome.strip():
        raise ValueError("Informe o nome.")
    nome = nome.strip()
    # Compara sem diferenciar maiúsculas/minúsculas ("Sala 01" = "sala 01").
    if any(l["nome"].casefold() == nome.casefold()
           for l in banco.consultar(f"SELECT nome FROM {tabela}")):
        raise ValueError("Já existe um consultório com esse nome."
                         if tabela == "consultorios"
                         else "Já existe uma especialidade com esse nome.")
    return banco.executar(f"INSERT INTO {tabela}(nome) VALUES (?)", (nome,))

def vincular(cid, eid):
    with banco.conectar() as con:
        con.execute("BEGIN IMMEDIATE")
        if con.execute("SELECT 1 FROM vinculos WHERE consultorio=? AND especialidade=?", (cid,eid)).fetchone():
            raise ValueError("Vínculo já cadastrado.")
        if con.execute("SELECT COUNT(*) FROM vinculos WHERE consultorio=?", (cid,)).fetchone()[0] >= 3:
            raise ValueError("Máximo de três especialidades por consultório.")
        con.execute("INSERT INTO vinculos VALUES (?,?)", (cid,eid))

def cadastrar_especialista(nome, usuario, senha, cid, eid):
    if not all(x.strip() for x in (nome, usuario, senha)):
        raise ValueError("Preencha todos os campos.")
    return banco.executar("""INSERT INTO especialistas(nome, usuario, senha, consultorio, especialidade)
        VALUES (?,?,?,?,?)""", (nome.strip(),usuario.strip(),senha,cid,eid))

def remover_especialista(sid):
    with banco.conectar() as con:
        con.execute("BEGIN IMMEDIATE")
        dados = con.execute("SELECT especialidade FROM especialistas WHERE id=?", (sid,)).fetchone()
        if not dados:
            raise ValueError("Especialista inexistente.")
        eid = dados[0]
        if con.execute("SELECT 1 FROM senhas WHERE especialidade=? AND status='Aguardando'", (eid,)).fetchone():
            if con.execute("SELECT COUNT(*) FROM especialistas WHERE especialidade=?", (eid,)).fetchone()[0] == 1:
                raise ValueError("Há pacientes aguardando o último especialista.")
        con.execute("DELETE FROM especialistas WHERE id=?", (sid,))

def mensagem_erro(erro):
    """Troca mensagens técnicas do SQLite por textos claros para o usuário."""
    texto = str(erro)
    if isinstance(erro, sqlite3.IntegrityError):
        if "UNIQUE" in texto:
            if "consultorios.nome" in texto:
                return "Já existe um consultório com esse nome."
            if "especialidades.nome" in texto:
                return "Já existe uma especialidade com esse nome."
            if "especialistas.usuario" in texto:
                return "Esse nome de usuário já está em uso."
            return "Já existe um registro com esses dados."
        if "FOREIGN KEY" in texto:
            return ("Não foi possível concluir: o registro está em uso por "
                    "outros dados (especialistas, senhas emitidas ou "
                    "atendimentos). Ajuste ou remova esses itens antes.")
    return texto
