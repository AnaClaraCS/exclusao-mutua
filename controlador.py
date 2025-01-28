import subprocess
import time
import re
from datetime import datetime
import os

NUM_PROCESSOS = 5  
REPETICOES = 10    
PROCESSO_SCRIPT = "processo.py" 
def iniciar_processos(n, r):
    processos = []
    for processo_id in range(1, n + 1):
        print(f"Iniciando Processo {processo_id}")
        processo = subprocess.Popen(
            ["python", PROCESSO_SCRIPT, str(processo_id), str(r)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processos.append(processo)
        #time.sleep(0.1)  # Pequeno intervalo para evitar sobrecarga inicial

    return processos

def aguardar_processos(processos):
    for i, processo in enumerate(processos, start=1):
        print(f"Aguardando finalização do Processo {i}...")
        processo.wait()
        print(f"Processo {i} finalizado.")

# Função para verificar o log do coordenador
def verificar_log(arquivo_log):
    try:
        with open(arquivo_log, "r", encoding="utf-8") as f:
            linhas = f.readlines()

        request_processos = []
        grant_processos = []
        release_processos = []

        # Processar as mensagens no log
        for linha in linhas:
            match = re.search(r"\[(.*?)\] (\d+) \| Processo: (\d+) \| Mensagem: (.*)", linha)
            if match:
                tipo = int(match.group(2))
                processo = int(match.group(3))

                if tipo == 1:  # REQUEST
                    request_processos.append(processo)
                elif tipo == 2:  # GRANT
                    grant_processos.append(processo)
                elif tipo == 3:  # RELEASE
                    release_processos.append(processo)

        # Verificar se GRANT e RELEASE estão intercalados
        if len(grant_processos) != len(release_processos):
            print("Erro: O número de mensagens GRANT e RELEASE não é igual.")
            return False

        for i in range(len(grant_processos)):
            if grant_processos[i] != release_processos[i]:
                print(f"Erro: Após o GRANT para o processo {grant_processos[i]}, o RELEASE ocorreu para o processo {release_processos[i]}.")
                return False

        # Verificar se a ordem de REQUEST é a mesma de RELEASE
        if request_processos != release_processos:
            print("Erro: A ordem dos processos nas mensagens REQUEST e RELEASE não coincide.")
            return False

        print("O log do coordenador está correto.")
        return True

    except FileNotFoundError:
        print(f"Erro: O arquivo {arquivo_log} não foi encontrado.")
        return False


# Função para verificar o resultado.txt
def verificar_resultado(arquivo_resultado, n):
    try:
        with open(arquivo_resultado, "r", encoding="utf-8") as f:
            linhas = f.readlines()

        if len(linhas) != n:
            print(f"Erro: O arquivo deve ter {n} linhas, mas possui {len(linhas)}.")
            return False

        processos_vistos = []
        timestamps = []

        for linha in linhas:
            match = re.search(r"Processo (\d+) - (.*?)$", linha.strip())
            if match:
                processo = int(match.group(1))
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
            print("Erro: A ordem dos timestamps no arquivo não respeita a evolução do relógio.")
            return False

        print("O arquivo resultado.txt está correto.")
        return True

    except FileNotFoundError:
        print(f"Erro: O arquivo {arquivo_resultado} não foi encontrado.")
        return False

if __name__ == "__main__":
    print("Iniciando controladora...")

    # Excluir arquivos de resultado e log
    # Excluir arquivos de resultado e log
    arquivos = ["resultado.txt", "coordenador.log"]
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            os.remove(arquivo)
            print(f"{arquivo} excluído.")
        else:
            print(f"{arquivo} não encontrado.")

    processos = iniciar_processos(NUM_PROCESSOS, REPETICOES)
    aguardar_processos(processos)
    print("Todos os processos finalizaram.")
    print("Execução concluída. Verifique o arquivo resultado.txt.")
    verificar_log("coordenador.log")
    verificar_resultado("resultado.txt", NUM_PROCESSOS * REPETICOES)
