import socket
import threading
import hashlib
import hmac
import os
import time
from datetime import datetime


class SecureChatServer:
    def __init__(self, host='0.0.0.0', port=65432):
        self.host = host
        self.port = port
        self.sessions = {}
        self.clients = []  # Lista de clientes conectados
        self.lock = threading.Lock()

    def vernam_encrypt_decrypt(self, data, key):
        return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])

    def derive_key(self, password, salt):
        return hashlib.pbkdf2_hmac('sha256', password, salt, 100000, 32)

    def verify_hmac(self, message, received_hmac, key):
        expected_hmac = hmac.new(key, message, hashlib.sha256).digest()
        return hmac.compare_digest(expected_hmac, received_hmac)

    def broadcast_message(self, message, sender_session_id=None):
        """Reenvía un mensaje a todos los clientes excepto al remitente"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        with self.lock:
            for client in self.clients[:]:  # Copia de la lista para evitar problemas durante iteración
                try:
                    if client['session_id'] != sender_session_id:
                        # Formatear mensaje para el receptor
                        if sender_session_id:
                            sender_addr = self.get_client_address(sender_session_id)
                            formatted_msg = f"[{timestamp}] {sender_addr}: {message}"
                        else:
                            formatted_msg = f"[{timestamp}] SISTEMA: {message}"

                        # Cifrar y enviar
                        encrypted_msg = self.encrypt_message(
                            formatted_msg.encode('utf-8'),
                            client['session_key'],
                            client['nonce_counter'] + 1
                        )
                        client['connection'].send(encrypted_msg)
                        client['nonce_counter'] += 1
                except Exception as e:
                    print(f"[-] Error enviando a {client['address']}: {e}")
                    self.remove_client(client['session_id'])

    def get_client_address(self, session_id):
        """Obtiene la dirección de un cliente por su session_id"""
        for client in self.clients:
            if client['session_id'] == session_id:
                return client['address']
        return "Desconocido"

    def add_client(self, conn, addr, session_id, session_key):
        """Agrega un cliente a la lista de conectados"""
        with self.lock:
            self.clients.append({
                'connection': conn,
                'address': addr,
                'session_id': session_id,
                'session_key': session_key,
                'nonce_counter': 0
            })
        print(f'[+] Cliente {addr} agregado. Total: {len(self.clients)}')
        self.broadcast_message(f"Usuario {addr} se ha unido al chat")

    def remove_client(self, session_id):
        """Elimina un cliente de la lista"""
        with self.lock:
            for client in self.clients[:]:
                if client['session_id'] == session_id:
                    self.clients.remove(client)
                    addr = client['address']
                    print(f'[+] Cliente {addr} removido. Total: {len(self.clients)}')
                    self.broadcast_message(f"Usuario {addr} ha dejado el chat")
                    break

    def handle_client(self, conn, addr):
        session_id = None
        try:
            print(f'[+] Nueva conexion de {addr}')

            # Establecimiento seguro de sesión
            salt = os.urandom(16)
            conn.send(salt)

            client_nonce = conn.recv(16)
            if len(client_nonce) != 16:
                raise ValueError("Nonce invalido")

            server_nonce = os.urandom(16)
            conn.send(server_nonce)

            master_key = b'Luciernagas_GlobalFinance_2024'
            session_key = self.derive_key(master_key, salt + client_nonce + server_nonce)

            session_id = hashlib.sha256(client_nonce + server_nonce).digest()[:8]
            self.sessions[session_id] = {
                'session_key': session_key,
                'last_nonce': 0,
                'start_time': time.time()
            }

            conn.send(session_id)

            # Agregar cliente a la lista
            self.add_client(conn, addr, session_id, session_key)

            # Comunicación segura
            while True:
                encrypted_data = conn.recv(1024)
                if not encrypted_data:
                    break

                if len(encrypted_data) < 48:
                    continue

                message_nonce = encrypted_data[:8]
                received_hmac = encrypted_data[8:40]
                encrypted_message = encrypted_data[40:]

                nonce_value = int.from_bytes(message_nonce, 'big')
                if nonce_value <= self.sessions[session_id]['last_nonce']:
                    continue

                self.sessions[session_id]['last_nonce'] = nonce_value

                if not self.verify_hmac(encrypted_message, received_hmac, session_key):
                    continue

                decrypted_message = self.vernam_encrypt_decrypt(encrypted_message, session_key)

                try:
                    message_text = decrypted_message.decode('utf-8')

                    # **REENVIAR mensaje a todos los clientes (excepto al remitente)**
                    self.broadcast_message(message_text, sender_session_id=session_id)

                    # Confirmación al remitente
                    ack_msg = f"Tu mensaje fue enviado a {len(self.clients) - 1} personas"
                    encrypted_ack = self.encrypt_message(ack_msg.encode('utf-8'), session_key, nonce_value + 1)
                    conn.send(encrypted_ack)

                except UnicodeDecodeError:
                    error_msg = "ERROR: Mensaje corrupto"
                    encrypted_error = self.encrypt_message(error_msg.encode('utf-8'), session_key, nonce_value + 1)
                    conn.send(encrypted_error)

        except Exception as e:
            print(f'[-] Error con {addr}: {e}')
        finally:
            if session_id:
                self.remove_client(session_id)
                if session_id in self.sessions:
                    del self.sessions[session_id]
            conn.close()

    def encrypt_message(self, message, key, nonce):
        encrypted = self.vernam_encrypt_decrypt(message, key)
        message_hmac = hmac.new(key, encrypted, hashlib.sha256).digest()
        nonce_bytes = nonce.to_bytes(8, 'big')
        return nonce_bytes + message_hmac + encrypted

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(5)
            print(f'[+] Servidor de chat grupal escuchando en {self.host}:{self.port}')
            print(f'[+] Los mensajes se reenvían entre clientes')

            try:
                while True:
                    conn, addr = s.accept()
                    client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                    client_thread.daemon = True
                    client_thread.start()
            except KeyboardInterrupt:
                print('\n[+] Cerrando servidor...')
                print(f'[+] Desconectando {len(self.clients)} clientes...')
            finally:
                s.close()


if __name__ == "__main__":
    server = SecureChatServer()
    server.start_server()