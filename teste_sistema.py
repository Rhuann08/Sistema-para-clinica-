import sqlite3
import unittest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import banco, cadastros, atendimentos
from prioridades import ordenar_fila
from tempo_espera import estimar, media

class TesteClinica(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original = banco.ARQUIVO
        banco.ARQUIVO = Path(self.tmp.name)/"teste.db"
        banco.iniciar()
        self.eid = banco.consultar("SELECT id FROM especialidades WHERE nome='Clínica Geral'")[0][0]
        self.cid = cadastros.cadastrar_nome("consultorios","Sala 01")
        cadastros.vincular(self.cid,self.eid)
        self.sid = cadastros.cadastrar_especialista("Carlos","carlos","1234",self.cid,self.eid)
    def tearDown(self):
        banco.ARQUIVO = self.original
        self.tmp.cleanup()
    def test_prioridade_fifo_numeracao(self):
        ids = []
        for cat in ("Normal","Gestante","Idoso com 80 anos ou mais","Normal","Idoso com 80 anos ou mais"):
            ids.append(atendimentos.emitir(self.eid,cat))
        self.assertEqual([n for _,n in ids],["N001","P001","P002","N002","P003"])
        fila = ordenar_fila(banco.consultar("SELECT * FROM senhas"))
        self.assertEqual([x["numero"] for x in fila],["P002","P003","P001","N001","N002"])
        self.assertEqual(estimar(self.eid,ids[0][0]),(90,3,"Sala 01"))
        self.assertEqual(atendimentos.chamar(self.sid)["numero"],"P002")
        with self.assertRaises(ValueError):
            atendimentos.chamar(self.sid)
        inicio = (datetime.now()-timedelta(minutes=20)).isoformat()
        banco.executar("UPDATE senhas SET inicio=? WHERE status='Em atendimento'",(inicio,))
        atendimentos.finalizar(self.sid)
        self.assertAlmostEqual(media(self.sid),20,places=1)
        self.assertEqual(atendimentos.chamar(self.sid)["numero"],"P003")
    def test_fila_vazia(self):
        with self.assertRaises(ValueError):
            atendimentos.chamar(self.sid)
        with self.assertRaises(ValueError):
            atendimentos.finalizar(self.sid)
    def test_limite_e_sem_especialista(self):
        for e in banco.consultar("SELECT id FROM especialidades WHERE id!=?",(self.eid,)):
            cadastros.vincular(self.cid,e[0])
            with self.assertRaises(ValueError):
                atendimentos.emitir(e[0],"Normal")
        extra = cadastros.cadastrar_nome("especialidades","Dermatologia")
        with self.assertRaises(ValueError):
            cadastros.vincular(self.cid,extra)
    def test_persistencia(self):
        atendimentos.emitir(self.eid,"Normal")
        banco.iniciar()
        self.assertEqual(len(banco.consultar("SELECT * FROM senhas")),1)

class TesteComplementar(unittest.TestCase):
    """Regras adicionais: duplicidade, mensagens, status, múltiplos especialistas."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original = banco.ARQUIVO
        banco.ARQUIVO = Path(self.tmp.name)/"teste.db"
        banco.iniciar()
        self.eid = banco.consultar("SELECT id FROM especialidades WHERE nome='Clínica Geral'")[0][0]
        self.cid = cadastros.cadastrar_nome("consultorios","Sala 01")
        cadastros.vincular(self.cid,self.eid)
        self.sid = cadastros.cadastrar_especialista("Carlos","carlos","1234",self.cid,self.eid)
    def tearDown(self):
        banco.ARQUIVO = self.original
        self.tmp.cleanup()

    def _segundo_especialista(self):
        cid2 = cadastros.cadastrar_nome("consultorios","Sala 02")
        cadastros.vincular(cid2,self.eid)
        return cadastros.cadastrar_especialista("Dora","dora","1234",cid2,self.eid)

    def _gastar_minutos(self, minutos):
        inicio = (datetime.now()-timedelta(minutes=minutos)).isoformat()
        banco.executar("UPDATE senhas SET inicio=? WHERE status='Em atendimento'",(inicio,))

    def test_nomes_duplicados_sem_diferenciar_caixa(self):
        with self.assertRaises(ValueError):
            cadastros.cadastrar_nome("consultorios","sala 01")
        with self.assertRaises(ValueError):
            cadastros.cadastrar_nome("especialidades","CLÍNICA GERAL")

    def test_campos_vazios(self):
        with self.assertRaises(ValueError):
            cadastros.cadastrar_nome("consultorios","   ")
        with self.assertRaises(ValueError):
            cadastros.cadastrar_especialista("","ana","1234",self.cid,self.eid)
        with self.assertRaises(ValueError):
            cadastros.cadastrar_especialista("Ana","ana","  ",self.cid,self.eid)

    def test_mensagens_claras_para_erros_do_banco(self):
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            cadastros.cadastrar_especialista("Outro","carlos","1234",self.cid,self.eid)
        self.assertEqual(cadastros.mensagem_erro(ctx.exception),"Esse nome de usuário já está em uso.")
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            banco.executar("DELETE FROM consultorios WHERE id=?",(self.cid,))
        self.assertIn("está em uso",cadastros.mensagem_erro(ctx.exception))
        self.assertEqual(cadastros.mensagem_erro(ValueError("texto")),"texto")

    def test_status_da_senha_ao_longo_do_atendimento(self):
        sid_senha,_ = atendimentos.emitir(self.eid,"Normal")
        status = lambda: banco.consultar("SELECT status FROM senhas WHERE id=?",(sid_senha,))[0][0]
        self.assertEqual(status(),"Aguardando")
        atendimentos.chamar(self.sid)
        self.assertEqual(status(),"Em atendimento")
        atendimentos.finalizar(self.sid)
        self.assertEqual(status(),"Atendido")
        self.assertEqual(len(banco.consultar("SELECT * FROM atendimentos")),1)

    def test_numeracao_independente_por_especialidade(self):
        outra = banco.consultar("SELECT id FROM especialidades WHERE nome='Cardiologia'")[0][0]
        cadastros.vincular(self.cid,outra)
        cadastros.cadastrar_especialista("Eva","eva","1234",self.cid,outra)
        self.assertEqual(atendimentos.emitir(self.eid,"Normal")[1],"N001")
        self.assertEqual(atendimentos.emitir(outra,"Normal")[1],"N001")
        self.assertEqual(atendimentos.emitir(outra,"Gestante")[1],"P001")
        self.assertEqual(atendimentos.emitir(self.eid,"Normal")[1],"N002")

    def test_chegada_prioritaria_nao_interrompe_consulta_em_andamento(self):
        atendimentos.emitir(self.eid,"Normal")
        self.assertEqual(atendimentos.chamar(self.sid)["numero"],"N001")
        atendimentos.emitir(self.eid,"Idoso com 80 anos ou mais")
        with self.assertRaises(ValueError):
            atendimentos.chamar(self.sid)
        atendimentos.finalizar(self.sid)
        self.assertEqual(atendimentos.chamar(self.sid)["numero"],"P001")

    def test_dois_especialistas_nao_chamam_a_mesma_senha(self):
        outro = self._segundo_especialista()
        atendimentos.emitir(self.eid,"Normal"); atendimentos.emitir(self.eid,"Normal")
        primeiro = atendimentos.chamar(self.sid)["numero"]
        segundo = atendimentos.chamar(outro)["numero"]
        self.assertEqual((primeiro,segundo),("N001","N002"))

    def test_previsao_considera_todos_os_especialistas(self):
        self._segundo_especialista()
        ids = [atendimentos.emitir(self.eid,"Normal")[0] for _ in range(3)]
        self.assertEqual(estimar(self.eid,ids[0])[:2],(0,0))
        self.assertEqual(estimar(self.eid,ids[1])[:2],(0,1))
        self.assertEqual(estimar(self.eid,ids[2])[:2],(30,2))

    def test_media_e_individual_por_especialista(self):
        outro = self._segundo_especialista()
        atendimentos.emitir(self.eid,"Normal")
        atendimentos.chamar(self.sid)
        self._gastar_minutos(10)
        atendimentos.finalizar(self.sid)
        self.assertAlmostEqual(media(self.sid),10,places=1)
        self.assertEqual(media(outro),30)

    def test_nao_remove_o_ultimo_especialista_com_fila(self):
        atendimentos.emitir(self.eid,"Normal")
        with self.assertRaises(ValueError):
            cadastros.remover_especialista(self.sid)
        outro = self._segundo_especialista()
        cadastros.remover_especialista(outro)      # há outro atendendo: permitido


if __name__ == "__main__":
    unittest.main(verbosity=2)
