const socket = io();
let username = '';
let connected = false;

// Elementos del DOM
const loginScreen = document.getElementById('login-screen');
const chatScreen = document.getElementById('chat-screen');
const usernameInput = document.getElementById('username-input');
const joinBtn = document.getElementById('join-btn');
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const statusEl = document.getElementById('status');

// Unirse al chat
joinBtn.addEventListener('click', () => {
    username = usernameInput.value.trim();
    if (username) {
        socket.emit('join_chat', { username: username });
    } else {
        alert('Por favor ingresa un nombre de usuario');
    }
});

// Enter para unirse
usernameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        joinBtn.click();
    }
});

// Conexión exitosa
socket.on('join_success', (data) => {
    connected = true;
    loginScreen.classList.add('hidden');
    chatScreen.style.display = 'flex';
    statusEl.textContent = '● Conectado';
    statusEl.classList.remove('disconnected');
    statusEl.classList.add('connected');
    addSystemMessage('Te has unido al chat seguro');
    messageInput.focus();
});

// Error de conexión
socket.on('join_error', (data) => {
    alert(data.message);
});

// Nuevo mensaje
socket.on('new_message', (data) => {
    addMessage(data.message, false);
});

// Aviso de desconexión
socket.on('disconnect_notice', (data) => {
    addSystemMessage(data.message);
    connected = false;
    statusEl.textContent = '● Desconectado';
    statusEl.classList.remove('connected');
    statusEl.classList.add('disconnected');
});

// Enviar mensaje
function sendMessage() {
    const message = messageInput.value.trim();
    if (message && connected) {
        socket.emit('send_message', { message: message });
        addMessage(message, true);
        messageInput.value = '';
    }
}

sendBtn.addEventListener('click', sendMessage);

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Agregar mensaje al chat
function addMessage(text, isOwn = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isOwn ? 'own' : ''}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const timeSpan = document.createElement('div');
    timeSpan.className = 'message-time';
    timeSpan.textContent = new Date().toLocaleTimeString('es-ES', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = text;
    
    contentDiv.appendChild(timeSpan);
    contentDiv.appendChild(textDiv);
    messageDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Agregar mensaje del sistema
function addSystemMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Auto-enfoque en el input al cargar
usernameInput.focus();