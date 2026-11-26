import sqlite3
from pathlib import Path
from contextlib import contextmanager

ARQUIVO = Path(__file__).with_name("clinica.db")

@contextmanager
def conectar():
    con = sqlite3.connect(ARQUIVO)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        with con:
            yield con
    finally:
        con.close()

def consultar(sql, dados=()):
    with conectar() as con:
        return con.execute(sql, dados).fetchall()

def executar(sql, dados=()):
    with conectar() as con:
        return con.execute(sql, dados).lastrowid

def iniciar():
    with conectar() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS consultorios(
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS especialidades(
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS vinculos(
            consultorio INTEGER REFERENCES consultorios(id) ON DELETE CASCADE,
            especialidade INTEGER REFERENCES especialidades(id) ON DELETE CASCADE,
            PRIMARY KEY(consultorio, especialidade));
        CREATE TABLE IF NOT EXISTS especialistas(
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL, senha TEXT NOT NULL,
            consultorio INTEGER NOT NULL REFERENCES consultorios(id),
            especialidade INTEGER NOT NULL REFERENCES especialidades(id),
            FOREIGN KEY(consultorio, especialidade) REFERENCES vinculos(consultorio, especialidade));
        CREATE TABLE IF NOT EXISTS senhas(
            id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT NOT NULL,
            especialidade INTEGER NOT NULL REFERENCES especialidades(id),
            categoria TEXT NOT NULL, prioridade INTEGER NOT NULL,
            chegada TEXT NOT NULL, inicio TEXT, fim TEXT,
            especialista INTEGER REFERENCES especialistas(id),
            status TEXT NOT NULL DEFAULT 'Aguardando',
            UNIQUE(especialidade, numero));
        CREATE TABLE IF NOT EXISTS atendimentos(
            especialista INTEGER REFERENCES especialistas(id),
            consultorio TEXT NOT NULL, hora_entrada TEXT NOT NULL,
            hora_saida TEXT NOT NULL, tempo_sala REAL NOT NULL);
        """)
        if con.execute("PRAGMA user_version").fetchone()[0] == 0:
            for nome in ("Clínica Geral", "Cardiologia", "Ortopedia"):
                con.execute("INSERT INTO especialidades(nome) VALUES (?)", (nome,))
            con.execute("PRAGMA user_version = 1")
