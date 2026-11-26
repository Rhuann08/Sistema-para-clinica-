# Sistema de Gerenciamento de Senhas — Clínica Médica

Projeto acadêmico da disciplina **Estrutura de Dados II** — Centro Universitário do Distrito Federal (UDF).
Sistema em **Python + Tkinter + SQLite** que organiza pacientes em filas de atendimento por especialidade,
com **prioridades atendidas por uma árvore binária heap mínimo combinada com filas FIFO**, e que estima o
tempo de espera de cada paciente a partir do tempo real das consultas já realizadas.

## Sumário

1. [Como executar](#como-executar)
2. [Roteiro de teste rápido](#roteiro-de-teste-rápido)
3. [Perfis de acesso](#perfis-de-acesso)
4. [Regras de prioridade](#regras-de-prioridade)
5. [Estruturas de dados](#estruturas-de-dados)
6. [Cálculo do tempo de espera](#cálculo-do-tempo-de-espera)
7. [Banco de dados](#banco-de-dados)
8. [Tratamento de erros](#tratamento-de-erros)
9. [Capturas de tela](#capturas-de-tela)
10. [Testes automatizados](#testes-automatizados)
11. [Estrutura do projeto](#estrutura-do-projeto)
12. [Divisão da equipe](#divisão-da-equipe)
13. [Limitações conhecidas](#limitações-conhecidas)
14. [Uso de IA](#uso-de-ia)

## Como executar

Requisitos: **Python 3.10 ou superior** com Tkinter (já incluído no instalador oficial do Python para Windows).
Não há pacotes externos para instalar.

```bash
python main.py
```

Se o comando não funcionar no Windows, use `py main.py`. O arquivo `clinica.db` é criado automaticamente na
primeira execução, na mesma pasta dos arquivos `.py`, e os dados são mantidos entre uma execução e outra.
Na primeira execução são cadastradas as especialidades *Clínica Geral*, *Cardiologia* e *Ortopedia*; o
administrador pode cadastrar, remover e organizar outras.

**Acesso do administrador:** usuário `admin`, senha `admin123`.

## Roteiro de teste rápido

1. No menu principal, entre como **Administrador**.
2. Em *Consultórios*, cadastre `Sala 01`.
3. Em *Especialidades*, escolha `Sala 01` e `Clínica Geral` e clique em **Vincular**.
4. Em *Especialistas*, cadastre `Carlos`, usuário `carlos`, senha `1234`, consultório `Sala 01` e especialidade `Clínica Geral`.
5. No menu, abra **Paciente** e gere, em *Clínica Geral*: `N001` (normal), `P001` (gestante), `P002` (idoso 80+), `N002` (normal) e `P003` (idoso 80+).
6. Abra **Especialista** e entre com `carlos` / `1234`.
7. A fila deve aparecer na ordem **P002, P003, P001, N001, N002**.
8. Use **Chamar próximo** e **Finalizar atendimento**; volte à área do paciente e consulte as senhas.
9. Teste os erros: chamar com a fila vazia, finalizar sem atendimento ativo, chamar com atendimento em andamento, campos vazios, quarto vínculo em um consultório e login inválido.

## Perfis de acesso

**Administrador** (tela de login própria)
- Cadastrar e remover consultórios e especialidades.
- Vincular especialidades a consultórios — **no máximo 3 especialidades por consultório**.
- Cadastrar especialistas com especialidade, consultório de atendimento, usuário e senha de acesso. Só aparecem para escolha as especialidades já vinculadas ao consultório.

**Paciente**
- Escolhe a especialidade e informa se a senha é **normal** ou **prioritária**; sendo prioritária, escolhe a categoria.
- A senha é exibida na tela com a especialidade, a categoria, o **consultório previsto**, os **pacientes à frente** e o **tempo estimado de espera**.
- Pode consultar a situação de qualquer senha: *Aguardando*, *Em atendimento* ou *Atendido*.

**Especialista** (login individual)
- Vê a fila da sua especialidade, na ordem exata de atendimento, com senha, categoria e horário de chegada. A tela se atualiza sozinha a cada 2 segundos.
- **Chama o próximo** paciente conforme as regras de prioridade e **finaliza** o atendimento; início e fim ficam registrados.
- Acompanha o histórico de atendimentos (com a duração em minutos) e a sua média de tempo por consulta.

## Regras de prioridade

| Nível | Categoria | Tipo da senha |
|:-----:|-----------|:-------------:|
| 1 | Idoso com 80 anos ou mais | Prioritária (`P`) |
| 2 | Demais idosos | Prioritária (`P`) |
| 3 | Pessoa com deficiência (PCD) | Prioritária (`P`) |
| 4 | Gestante | Prioritária (`P`) |
| 5 | Pessoa com criança de colo | Prioritária (`P`) |
| 6 | Atendimento normal | Normal (`N`) |

- Menor nível é atendido primeiro; **dentro do mesmo nível vale a ordem de chegada (FIFO)**.
- Uma chegada prioritária ultrapassa pacientes de nível menos urgente que ainda aguardam, mas **não interrompe uma consulta já iniciada**.
- A numeração é por especialidade e sem ambiguidade: `N001`, `N002`… para senhas normais e `P001`, `P002`… para prioritárias. A sequência `P` é única para as cinco categorias prioritárias.

## Estruturas de dados

O arquivo `prioridades.py` combina duas estruturas:

- **Árvore binária heap mínimo** (vetor, filhos de `i` em `2i+1` e `2i+2`) que guarda apenas os **níveis de prioridade que têm pacientes esperando**. A raiz é sempre o nível mais urgente.
- **Uma fila FIFO (`collections.deque`) por nível**, que preserva a ordem de chegada dentro da categoria.

```
        heap de níveis ativos            filas FIFO
             [ 2 ]                 1: —
            /     \                2: P005 → P009
         [ 4 ]   [ 6 ]             4: P001
                                   6: N001 → N002 → N003
```

Funcionamento:

- **Inserir:** o paciente entra no fim da fila do seu nível; se o nível estava vazio, ele sobe no heap (*sift-up*).
- **Retirar:** lê-se a raiz do heap, retira-se o primeiro da fila daquele nível e, se a fila esvaziou, o nível sai do heap (*sift-down*).
- Como existem no máximo 6 níveis, as operações no heap são de custo muito pequeno (O(log 6)), e a escolha do próximo paciente é O(1) na fila.
- `ordenar_fila()` reconstrói a estrutura a partir das senhas com situação *Aguardando* no banco e devolve a ordem de atendimento. A **mesma estrutura** é usada na chamada real, na exibição da fila do especialista e na estimativa de espera.

## Cálculo do tempo de espera

Implementado em `tempo_espera.py`, com `datetime`.

1. **Duração de cada consulta:** `tempo_sala = hora_saida − hora_entrada`, em minutos, gravada na tabela `atendimentos`.
2. **Média por especialista:** média dos `tempo_sala` já registrados; enquanto não há consultas, usa **30 minutos**. A cada consulta finalizada a média é atualizada.
3. **Simulação da fila:** considera **todos os especialistas** da especialidade. Cada um fica disponível após terminar o que está atendendo (média menos o tempo já decorrido). Os pacientes, na ordem da fila de prioridade, vão sendo atribuídos ao especialista que fica livre primeiro; cada atribuição soma a média daquele especialista.
4. **Resultado exibido ao paciente:** tempo estimado, quantidade de pacientes à frente e o consultório do especialista previsto.

O consultório mostrado antes da chamada é uma **previsão**; o definitivo é o do especialista que chamar a senha. O tempo é uma estimativa e varia conforme a duração real dos atendimentos.

## Banco de dados

SQLite local (`clinica.db`), com chaves estrangeiras ativas e criação automática das tabelas (`banco.py`):

| Tabela | Conteúdo |
|--------|----------|
| `consultorios` | id, nome (único) |
| `especialidades` | id, nome (único) |
| `vinculos` | consultório × especialidade (chave composta) |
| `especialistas` | nome, usuário (único), senha, consultório e especialidade (devem estar vinculados) |
| `senhas` | número (`N001`/`P001`), especialidade, categoria, nível de prioridade, chegada, início, fim, especialista e situação |
| `atendimentos` | especialista, consultório, `hora_entrada`, `hora_saida` e `tempo_sala` (minutos) |

## Tratamento de erros

As operações mostram uma mensagem ao usuário em vez de encerrar o programa. Casos cobertos:

- fila vazia ao chamar o próximo paciente;
- chamar um paciente enquanto já há atendimento em andamento;
- finalizar sem atendimento ativo;
- quarto vínculo em um consultório (limite de 3 especialidades);
- campos vazios, categoria de prioridade não escolhida e opções não selecionadas;
- login inválido (administrador e especialista);
- nome repetido de consultório, especialidade ou usuário (sem diferenciar maiúsculas e minúsculas);
- remoção de consultório, especialidade ou especialista que ainda estão em uso;
- emissão de senha em especialidade sem especialista, e remoção do último especialista com pacientes aguardando.

## Capturas de tela

Capturas feitas com dados de demonstração (3 especialistas, 9 senhas emitidas e consultas já finalizadas).

| | |
|---|---|
| ![Menu principal](docs/img/01_menu_principal.png) | ![Administrador — consultórios](docs/img/02_admin_consultorios.png) |
| **Menu principal:** escolha entre administrador, especialista e paciente | **Administrador:** consultórios |
| ![Administrador — especialidades e vínculos](docs/img/03_admin_especialidades_vinculos.png) | ![Administrador — especialistas](docs/img/04_admin_especialistas.png) |
| **Administrador:** especialidades e vínculos (máximo de 3 por consultório) | **Administrador:** especialistas |
| ![Paciente](docs/img/05_paciente_senha_prioritaria.png) | ![Login do especialista](docs/img/06_login_especialista.png) |
| **Paciente:** senha prioritária com consultório previsto, pacientes à frente e espera estimada | **Especialista:** login |
| ![Especialista — fila](docs/img/07_especialista_fila.png) | ![Especialista — em atendimento](docs/img/08_especialista_em_atendimento.png) |
| **Especialista:** fila ordenada por prioridade e histórico | **Especialista:** após chamar o próximo paciente |

## Testes automatizados

```bash
python -m unittest teste_sistema -v
```

São 14 testes que usam um banco SQLite temporário (o `clinica.db` real nunca é alterado). Cobrem: ordem de
prioridade e FIFO, numeração `N`/`P` por especialidade, estimativa de espera com um e com vários
especialistas, média individual por especialista, situação da senha (*Aguardando → Em atendimento → Atendido*),
dois especialistas que não chamam a mesma senha, fila vazia, finalização sem atendimento, limite de vínculos,
campos vazios, nomes duplicados, mensagens de erro e persistência dos dados.

## Estrutura do projeto

| Arquivo | Função |
|---------|--------|
| `main.py` | Menu principal: escolha do perfil (administrador, especialista ou paciente) |
| `banco.py` | Conexão e criação das tabelas do SQLite |
| `administrador.py` | Login e painel do administrador |
| `cadastros.py` | Regras de negócio dos cadastros e vínculos; tradução das mensagens de erro do banco |
| `paciente.py` | Emissão de senhas e consulta de situação |
| `especialista.py` | Login e painel do especialista |
| `atendimentos.py` | Emissão de senhas, chamada do próximo e finalização de consultas |
| `prioridades.py` | Heap mínimo + filas FIFO |
| `tempo_espera.py` | Duração das consultas, média por especialista e previsão de espera |
| `interface.py` | Componentes visuais reutilizáveis e janela padrão de login |
| `teste_sistema.py` | Testes automatizados com banco temporário |
| `docs/img/` | Capturas de tela usadas neste README |

## Divisão da equipe

| Integrante | Responsabilidade | Arquivos principais |
|------------|------------------|---------------------|
| **Rhuann Pabllo** | Área do administrador e área do paciente | `administrador.py`, `cadastros.py`, `paciente.py` |
| **Ryan Áquila** | Área do especialista e organização modular do código | `especialista.py`, `atendimentos.py`, `main.py`, `interface.py` |
| **Matheus Carvalho** | Sistema de prioridades (heap mínimo + FIFO) | `prioridades.py` |
| **João Victor Lima** | Cálculo do tempo de espera e persistência em SQLite | `tempo_espera.py`, `banco.py` |

## Limitações conhecidas

- O sistema é local: não sincroniza dados entre computadores e foi pensado para demonstração.
- As senhas de acesso dos especialistas ficam **em texto no banco**; não utilize dados reais.
- A regra de prioridade é a regra acadêmica do enunciado, não uma orientação de triagem clínica; ela pode gerar espera longa para pacientes de atendimento normal.
- O tempo de espera é uma estimativa; a tela do paciente é atualizada pelo botão *Consultar / atualizar*.

## Uso de IA

Foi usada assistência de IA (Claude) na elaboração da versão-base, na revisão e correção de problemas
encontrados ao testar as telas, nos testes complementares e na redação deste README. Cada integrante revisou e
é responsável pela sua parte.
