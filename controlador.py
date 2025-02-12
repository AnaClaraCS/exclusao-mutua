import subprocess
import time
import re
from datetime import datetime
import os

NUM_PROCESSOS = 5  
REPETICOES = 5
PROCESSO_SCRIPT = "processo.py" 

class LinhaLog: # Classe para armazenar informações de log
    def __init__(self, tipo, processo, timestamp):
        self.tipo = tipo
        self.processo = processo
        self.timestamp = timestamp

def iniciar_processos(n, r):
    processos = []
    for processo_id in range(1, n + 1):
        print(f"Iniciando Processo {processo_id}")
        processo = subprocess.Popen(
            ["python", PROCESSO_SCRIPT, str(processo_id), str(r)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        processos.append(processo)
        #time.sleep(0.1)  # Pequeno intervalo para evitar sobrecarga inicial

    return processos

def aguardar_processos(processos):
    for i, processo in enumerate(processos, start=1):
        #print(f"Aguardando finalização do Processo {i}...")
        processo.wait()
        print(f"Processo {i} finalizado.")

# Função para verificar o log do coordenador
def verificar_log(arquivo_log):
    try:
        with open(arquivo_log, "r", encoding="utf-8") as f:
            linhas = f.readlines()

        # Processar as mensagens no log
        logs = []
        for linha in linhas:
            match = re.search(r"\[(.*?)\] - (\d+) - (REQUEST|GRANT|RELEASE)", linha)
            if match:
                timestamp = match.group(1)
                processo = int(match.group(2))
                tipo = match.group(3)
                logs.append(LinhaLog(tipo, processo, timestamp))

        # Verificar a ordem das mensagens para cada processo
        for i in range(1, NUM_PROCESSOS + 1):
            estado = "INICIO"
            for index, linha in enumerate(logs):
                if linha.processo == i:
                    #print(f'[Index {index}]{linha.processo} - estado {estado} - recebeu {linha.tipo}')
                    # Se o estado é {estado} e recebe um {linha.tipo} vai para {linha.tipo}
                    if estado == "INICIO" and linha.tipo == "REQUEST":
                        estado = "REQUEST"
                    elif estado == "REQUEST" and linha.tipo == "GRANT":
                        estado = "GRANT"
                    elif estado == "GRANT" and linha.tipo == "RELEASE":
                        estado = "RELEASE"
                    elif estado == "RELEASE" and linha.tipo == "REQUEST":
                        estado = "REQUEST"
                    else:
                        print(f"Erro: Processo {i} não segue a ordem correta, na linha {index + 1}")
                        return False

            if estado == "RELEASE":
                print(f"Processo {i} seguiu a sequência correta")
            else:
                print(f"Erro: Processo {i} não completou a sequência REQUEST -> GRANT -> RELEASE")
                return False

        print("\nO log do coordenador está correto\n")
        return True

    except FileNotFoundError:
        print(f"Erro: O arquivo {arquivo_log} não foi encontrado")
        return False

# Função para verificar o resultado.txt
def verificar_resultado(arquivo_resultado, n):
    try:
        with open(arquivo_resultado, "r", encoding="utf-8") as f:
            linhas = f.readlines()

        if len(linhas) != n:
            print(f"Erro: O arquivo deve ter {n} linhas, mas possui {len(linhas)}")
            return False

        timestamps = []

        for linha in linhas:
            match = re.search(r"Processo (\d+) - (.*?)$", linha.strip())
            if match:
                # processo = int(match.group(1))
                timestamp = match.group(2)

                # Verificar formato do timestamp
                try:
                    timestamps.append(datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f"))
                except ValueError:
                    print(f"Erro: Timestamp inválido no arquivo: {timestamp}.")
                    return False
            else:
                print(f"Erro: Linha inválida encontrada no arquivo: {linha.strip()}.")
                return False

        # Verificar ordem dos timestamps
        if timestamps != sorted(timestamps):
            print("Erro: A ordem dos timestamps no arquivo não respeita a evolução do relógio")
            return False

        print("O arquivo resultado.txt está correto\n")
        return True

    except FileNotFoundError:
        print(f"Erro: O arquivo {arquivo_resultado} não foi encontrado")
        return False

if __name__ == "__main__":
    print("Iniciando controlador...")

    # 1 - Excluir arquivos de resultado e log
    arquivos = ["resultado.txt", "coordenador.log"]
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            os.remove(arquivo)
            print(f"{arquivo} excluído")
        else:
            print(f"{arquivo} não encontrado")

    # 2 - Inicializa os processos e aguarda terminaram
    processos = iniciar_processos(NUM_PROCESSOS, REPETICOES)
    print(f"Aguardando finalização dos processos ...")
    aguardar_processos(processos)
    print("Todos os processos finalizaram\n")

    # 3 - Verifica se os arquivos gerados pelo coordenador estão
    verificar_log("coordenador.log")
    verificar_resultado("resultado.txt", NUM_PROCESSOS * REPETICOES)
