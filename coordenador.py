import socket
import threading
from queue import Queue
from datetime import datetime

HOST = "127.0.0.1"
PORT = 12345
F = 8  
processos_atendidos = {}
lock = threading.Lock()
fila_pedidos = Queue() #  thread-safe -> garante a sincronização de acesso à fila
fila_release = Queue() 
processos_na_rc = {}  # Dicionário para controlar região crítica

# Função para codificar a mensagem de acordo com o padrão
def codifica_mensagem(tipo, processo):
    return f"{tipo}|{processo}|".ljust(F, '0').encode()

# Função para extrair o tipo e o processo da mensagem
def decodifica_mensagem(mensagem):
    partes = mensagem.strip().split('|')
    return int(partes[0]), int(partes[1])

# Função para registrar logs
def registrar_log(tipo, processo):
    with open("coordenador.log", "a", encoding="utf-8") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        if tipo == 1:
            mensagem = "REQUEST"
        elif tipo == 2:
            mensagem = "GRANT"
        elif tipo == 3:
            mensagem = "RELEASE"

        log_file.write(
           f"{mensagem} - {processo} - [{timestamp}]\n"
        )

# Thread para gerenciar conexões
def gerenciar_conexoes(server_socket):
    while True:
        data, client_address = server_socket.recvfrom(1024) 
        mensagem = data.decode().strip()
        print(f"Recebido: {mensagem} de {client_address}")
        
        tipo, processo = decodifica_mensagem(mensagem)
        
        with lock: # Para contar quantas vezes cada processo foi atendido
            if processo not in processos_atendidos:
                processos_atendidos[processo] = 0

        if tipo == 1:  # REQUEST
            fila_pedidos.put({'processo': processo, 'endereco': client_address})
            registrar_log(1, processo)
        elif tipo == 3:  # RELEASE
            with lock: # Registra que um processo liberou a região crítica
                if processo in processos_na_rc:
                    processos_na_rc[processo]['release'] = True 
            registrar_log(3, processo)

# Thread para executar o algoritmo de exclusão mútua
def executar_algoritmo(server_socket):
    while True:
        if not fila_pedidos.empty():
            requisicao = fila_pedidos.get()
            processo = requisicao['processo']
            endereco = requisicao['endereco']
            
            # Conceder acesso à região crítica 
            mensagem = codifica_mensagem(2, processo)  # 2 = GRANT
            registrar_log(2, processo)
            with lock:
                processos_atendidos[processo] += 1
                processos_na_rc[processo] = {'endereco': endereco, 'release': False}
                server_socket.sendto(mensagem, endereco)

            # Aguardar o RELEASE
            while True:
                with lock:
                    if processos_na_rc[processo]['release']:
                        del processos_na_rc[processo]
                        break

# Thread para interface do terminal
def interface_terminal():
    while True:
        comando = int(input("\n\n 1) imprimir a fila de pedidos atual \n 2) imprimir quantas vezes cada processo foi atendido \n 3) encerrar a execução \n Opção: "))
        if comando == 1:
            print("\n\nFila atual:")
            with lock:
                for item in list(fila_pedidos.queue):
                    print(item)
        elif comando == 2:
            with lock:
                print("\n\nEstatísticas de atendimentos:")
                for processo, count in processos_atendidos.items():
                    print(f"Processo {processo}: {count} vez(es)")
        elif comando == 3:
            print("\n\nEncerrando coordenador...")
            break
        else:
            print("Comando inválido!")

if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))

    thread_conexoes = threading.Thread(target=gerenciar_conexoes, args=(server_socket,))
    thread_conexoes.start()

    thread_algoritmo = threading.Thread(target=executar_algoritmo, args=(server_socket,))
    thread_algoritmo.start()

    thread_terminal = threading.Thread(target=interface_terminal)
    thread_terminal.start()

    thread_terminal.join() 
    print("Coordenador encerrado.")
