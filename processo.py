import socket
import time
from datetime import datetime
import sys
import random  

HOST = "127.0.0.1"  
PORT = 12345 
F = 8 

def codifica_mensagem(tipo, processo_id):
    return f"{tipo}|{processo_id}|".ljust(F, '0').encode()

def main(processo_id, r):
    # Criação do socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        print(f"Processo {processo_id} iniciado.")
        
        for i in range(r):
            # Enviar REQUEST ao coordenador
            mensagem_request = codifica_mensagem("1", processo_id)  # 1 = REQUEST
            client_socket.sendto(mensagem_request, (HOST, PORT))
            print(f"Processo {processo_id} enviou REQUEST ({i + 1}/{r})")

            # Aguardar GRANT do coordenador
            while True:
                data, _ = client_socket.recvfrom(1024)
                resposta = data.decode().strip()
                if resposta.startswith("2"):  # 2 = GRANT
                    print(f"Processo {processo_id} recebeu GRANT ({i + 1}/{r}).")
                    break
            
            # Região crítica
            with open("resultado.txt", "a",encoding="utf-8") as arquivo:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                arquivo.write(f"Processo {processo_id} - {timestamp}\n")
                print(f"Processo {processo_id} escreveu no arquivo: {timestamp}")
            
            # Espera aleatória dentro da região crítica
            espera_rc = random.uniform(1, 5)
            print(f"Processo {processo_id} aguardando {espera_rc:.2f}s dentro da região crítica.")
            time.sleep(espera_rc)

            # Enviar RELEASE ao coordenador
            mensagem_release = codifica_mensagem("3", processo_id)  # 3 = RELEASE
            client_socket.sendto(mensagem_release, (HOST, PORT))
            print(f"Processo {processo_id} enviou RELEASE ({i + 1}/{r}).")

            # Espera aleatória entre interações
            espera_interacao = random.uniform(1, 10)
            print(f"Processo {processo_id} aguardando {espera_interacao:.2f}s antes da próxima interação.")
            time.sleep(espera_interacao)

    print(f"Processo {processo_id} finalizou.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python processo.py <processo_id> <quantidade_requisicoes>")
        sys.exit(1)

    processo_id = int(sys.argv[1])
    r = int(sys.argv[2])

    main(processo_id, r)
