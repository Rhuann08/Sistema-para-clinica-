from collections import deque

PRIORIDADES = {
    "Idoso com 80 anos ou mais": 1,
    "Demais idosos": 2,
    "Pessoa com deficiência (PCD)": 3,
    "Gestante": 4,
    "Pessoa com criança de colo": 5,
    "Normal": 6
}

class FilaPrioridade:
    # Heap mínimo de categorias e uma fila FIFO para cada categoria.
    def __init__(self):
        self.arvore = []
        self.filas = {n: deque() for n in range(1, 7)}

    def inserir(self, paciente):
        p = paciente["prioridade"]
        if not self.filas[p]:
            self.arvore.append(p)
            i = len(self.arvore) - 1
            while i > 0:
                pai = (i - 1) // 2
                if self.arvore[pai] <= self.arvore[i]:
                    break
                self.arvore[pai], self.arvore[i] = self.arvore[i], self.arvore[pai]
                i = pai
        self.filas[p].append(paciente)

    def retirar(self):
        if not self.arvore:
            return None
        p = self.arvore[0]
        paciente = self.filas[p].popleft()
        if not self.filas[p]:
            ultimo = self.arvore.pop()
            if self.arvore:
                self.arvore[0] = ultimo
                i = 0
                while True:
                    menor = i
                    for filho in (2*i+1, 2*i+2):
                        if filho < len(self.arvore) and self.arvore[filho] < self.arvore[menor]:
                            menor = filho
                    if menor == i:
                        break
                    self.arvore[i], self.arvore[menor] = self.arvore[menor], self.arvore[i]
                    i = menor
        return paciente

def ordenar_fila(pacientes):
    fila = FilaPrioridade()
    for paciente in sorted(pacientes, key=lambda x: x["id"]):
        fila.inserir(paciente)
    resultado = []
    while fila.arvore:
        resultado.append(fila.retirar())
    return resultado
