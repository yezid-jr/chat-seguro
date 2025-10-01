from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import socket
import hashlib
import hmac
import os
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Almacena las conexiones activas de cada usuario web
active_connections = {}

class ChatClientBridge:
    """Puente entre el cliente web y el servidor de chat seguro"""
    
    def __init__(self, user_id, chat_server_host='127.0.0.1', chat_server_port=65432):
        self.user_id = user_id
        self.chat_server_host = chat_server_host
        self.chat_server_port = chat_server_port
        self.session_key = None
        self.nonce_counter = 0
        self.conn = None
        self.receiving = True
        
    def vernam_encrypt_decrypt(self, data, key):
        return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
    
    def derive_key(self, password, salt):
        return hashlib.pbkdf2_hmac('sha256', password, salt, 100000, 32)
    
    def establish_secure_session(self):
        try:
            salt = self.conn.recv(16)
            client_nonce = os.urandom(16)
            self.conn.send(client_nonce)
            server_nonce = self.conn.recv(16)
            
            master_key = b'Luciernagas_GlobalFinance_2024'
            self.session_key = self.derive_key(master_key, salt + client_nonce + server_nonce)
            
            session_id = self.conn.recv(8)
            return True
        except Exception as e:
            print(f'Error estableciendo sesión: {e}')
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
        
        received_hmac = encrypted_data[8:40]
        encrypted_message = encrypted_data[40:]
        
        expected_hmac = hmac.new(self.session_key, encrypted_message, hashlib.sha256).digest()
        if not hmac.compare_digest(expected_hmac, received_hmac):
            return None
        
        return self.vernam_encrypt_decrypt(encrypted_message, self.session_key)
    
    def receive_messages(self):
        """Hilo que recibe mensajes del servidor de chat y los envía al cliente web"""
        while self.receiving:
            try:
                data = self.conn.recv(1024)
                if not data:
                    socketio.emit('disconnect_notice', 
                                {'message': 'Conexión perdida con el servidor'}, 
                                room=self.user_id)
                    break
                
                decrypted = self.decrypt_message(data)
                if decrypted:
                    message = decrypted.decode('utf-8')
                    # Enviar mensaje al cliente web vía WebSocket
                    socketio.emit('new_message', {'message': message}, room=self.user_id)
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.receiving:
                    print(f'Error recibiendo mensaje: {e}')
                break
    
    def connect(self):
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.settimeout(1.0)
            self.conn.connect((self.chat_server_host, self.chat_server_port))
            
            if not self.establish_secure_session():
                return False
            
            # Iniciar hilo de recepción
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            return True
        except Exception as e:
            print(f'Error conectando: {e}')
            return False
    
    def send_message(self, message):
        try:
            encrypted = self.encrypt_message(message.encode('utf-8'))
            self.conn.send(encrypted)
            return True
        except Exception as e:
            print(f'Error enviando mensaje: {e}')
            return False
    
    def disconnect(self):
        self.receiving = False
        if self.conn:
            self.conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    user_id = request.sid
    print(f'Usuario web conectado: {user_id}')

@socketio.on('join_chat')
def handle_join_chat(data):
    user_id = request.sid
    username = data.get('username', f'Usuario_{user_id[:8]}')
    
    # Crear puente de conexión con el servidor de chat
    bridge = ChatClientBridge(user_id)
    
    if bridge.connect():
        active_connections[user_id] = bridge
        join_room(user_id)
        emit('join_success', {'message': f'Conectado como {username}'})
        print(f'{username} se unió al chat')
    else:
        emit('join_error', {'message': 'No se pudo conectar al servidor de chat'})

@socketio.on('send_message')
def handle_send_message(data):
    user_id = request.sid
    message = data.get('message', '')
    
    if user_id in active_connections:
        bridge = active_connections[user_id]
        if bridge.send_message(message):
            # El mensaje se mostrará cuando el servidor lo reenvíe
            pass
        else:
            emit('error', {'message': 'Error enviando mensaje'})
    else:
        emit('error', {'message': 'No estás conectado al chat'})

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid
    if user_id in active_connections:
        active_connections[user_id].disconnect()
        del active_connections[user_id]
        leave_room(user_id)
    print(f'Usuario web desconectado: {user_id}')

if __name__ == '__main__':
    print('[+] Servidor web iniciando en http://0.0.0.0:5000')
    print('[+] Asegúrate de que el servidor de chat esté corriendo en el puerto 65432')
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)