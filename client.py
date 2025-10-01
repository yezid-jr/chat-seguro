import socket
import hashlib
import hmac
import os
import sys
import threading
import time


class SecureChatClient:
    def __init__(self, server_host='127.0.0.1', server_port=65432):
        self.server_host = server_host
        self.server_port = server_port
        self.session_key = None
        self.nonce_counter = 0
        self.receiving = True
        self.username = f"Usuario_{os.getpid()}"  # Nombre único para cada cliente

    def vernam_encrypt_decrypt(self, data, key):
        return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])

    def derive_key(self, password, salt):
        return hashlib.pbkdf2_hmac('sha256', password, salt, 100000, 32)

    def establish_secure_session(self, conn):
        try:
            salt = conn.recv(16)
            client_nonce = os.urandom(16)
            conn.send(client_nonce)
            server_nonce = conn.recv(16)

            master_key = b'Luciernagas_GlobalFinance_2024'
            self.session_key = self.derive_key(master_key, salt + client_nonce + server_nonce)

            session_id = conn.recv(8)
            print(f'[+] Conectado al chat seguro. ID: {session_id.hex()}')
            return True

        except Exception as e:
            print(f'[-] Error estableciendo sesion: {e}')
            return False

    def encrypt_message(self, message):
        self.nonce_counter += 1
        encrypted = self.vernam_encrypt_decrypt(message, self.session_key)
        message_hmac = hmac.new(self.session_key, encrypted, hashlib.sha256).digest()
        nonce_bytes = self.nonce_counter.to_bytes(8, 'big')
        return nonce_bytes + message_hmac + encrypted

    def decrypt_message(self, encrypted_data):
        if len(encrypted_data) < 40:
            return None

        nonce = encrypted_data[:8]
        received_hmac = encrypted_data[8:40]
        encrypted_message = encrypted_data[40:]

        expected_hmac = hmac.new(self.session_key, encrypted_message, hashlib.sha256).digest()
        if not hmac.compare_digest(expected_hmac, received_hmac):
            return None

        return self.vernam_encrypt_decrypt(encrypted_message, self.session_key)

    def receive_messages(self, conn):
        """Hilo para recibir mensajes en tiempo real"""
        while self.receiving:
            try:
                data = conn.recv(1024)
                if not data:
                    print("\n[!] Conexion con el servidor perdida")
                    self.receiving = False
                    break

                decrypted = self.decrypt_message(data)
                if decrypted:
                    message = decrypted.decode('utf-8')
                    # Mostrar mensaje sin interrumpir la entrada
                    print(f"\n{message}\nTu: ", end="", flush=True)
                else:
                    print("\n[!] Mensaje corrupto recibido")

            except socket.timeout:
                continue
            except Exception as e:
                if self.receiving:
                    print(f"\n[!] Error recibiendo: {e}")
                break

    def start_client(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
                conn.settimeout(1.0)  # Timeout corto para verificar receiving
                print(f'[+] Conectando a {self.server_host}:{self.server_port}...')
                conn.connect((self.server_host, self.server_port))

                if not self.establish_secure_session(conn):
                    return

                # Establecer username
                username_msg = f"/username {self.username}"
                encrypted_username = self.encrypt_message(username_msg.encode('utf-8'))
                conn.send(encrypted_username)

                # Iniciar hilo para recibir mensajes
                receive_thread = threading.Thread(target=self.receive_messages, args=(conn,))
                receive_thread.daemon = True
                receive_thread.start()

                print('\n[+] === CHAT SEGURO ACTIVO ===')
                print('[+] Escribe tus mensajes (se enviarán a todos los conectados)')
                print('[+] Comandos: /exit, /status, /users\n')

                while self.receiving:
                    try:
                        message = input("Tu: ")

                        if message.lower() == '/exit':
                            self.receiving = False
                            break
                        elif message.lower() == '/status':
                            print(f'[Estado] Nonce: {self.nonce_counter}')
                            continue
                        elif message.lower() == '/users':
                            print('[Info] Consulta de usuarios disponible')
                            continue

                        if not message.strip():
                            continue

                        # Enviar mensaje al chat grupal
                        encrypted = self.encrypt_message(message.encode('utf-8'))
                        conn.send(encrypted)

                        # Esperar breve confirmación
                        time.sleep(0.1)

                    except KeyboardInterrupt:
                        print('\n[+] Desconectando...')
                        self.receiving = False
                        break
                    except Exception as e:
                        print(f'\n[-] Error: {e}')
                        self.receiving = False
                        break

                print('[+] Desconectado del chat')

        except ConnectionRefusedError:
            print('[-] No se pudo conectar al servidor')
        except Exception as e:
            print(f'[-] Error de conexion: {e}')


if __name__ == "__main__":
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
        print(f'[+] Usando servidor: {server_ip}')
        client = SecureChatClient(server_host=server_ip)
    else:
        client = SecureChatClient()

    client.start_client()