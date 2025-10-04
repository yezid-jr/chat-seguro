# Chat Seguro Americana

Sistema de chat grupal en tiempo real con cifrado end-to-end utilizando el cifrado Vernam (One-Time Pad), HMAC para autenticación de mensajes y nonces para prevenir ataques de repetición.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-red.svg)

## Tabla de Contenidos

- [Características](#-características)
- [Seguridad](#-seguridad)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Uso](#-uso)
- [Arquitectura](#-arquitectura)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## Características

### Seguridad
- **Cifrado Vernam (XOR)**: Cada mensaje se cifra con la clave de sesión
- **HMAC-SHA256**: Autenticación de integridad de mensajes
- **Nonces secuenciales**: Protección contra ataques de replay
- **Derivación de claves PBKDF2**: 100,000 iteraciones para máxima seguridad
- **Sesiones únicas**: Cada cliente tiene su propia clave de sesión derivada

### Chat
- **Tiempo real**: Mensajes instantáneos usando WebSockets
- **Multi-usuario**: Soporte para múltiples clientes simultáneos
- **Broadcast**: Los mensajes se envían a todos los usuarios conectados
- **Notificaciones**: Sistema de avisos cuando usuarios entran/salen
- **Interfaz moderna**: UI responsiva con animaciones suaves

### Multiplataforma
- **Cliente Web**: Interfaz visual moderna en el navegador
- **Cliente Terminal**: Interfaz CLI para usuarios avanzados
- **Cross-platform**: Compatible con Windows, Linux y macOS

---

## Seguridad

### Protocolo de Establecimiento de Sesión

```
1. Servidor → Cliente: Salt (16 bytes aleatorios)
2. Cliente → Servidor: Client Nonce (16 bytes aleatorios)
3. Servidor → Cliente: Server Nonce (16 bytes aleatorios)
4. Ambos derivan: Session Key = PBKDF2(master_key, salt+client_nonce+server_nonce)
5. Servidor → Cliente: Session ID (hash de nonces)
```

### Formato de Mensaje Cifrado

```
[Nonce: 8 bytes][HMAC: 32 bytes][Mensaje Cifrado: variable]
```

1. **Nonce**: Contador secuencial para prevenir replay attacks
2. **HMAC**: HMAC-SHA256(session_key, mensaje_cifrado)
3. **Mensaje Cifrado**: Vernam(mensaje_original, session_key)

### Validaciones de Seguridad

- ✅ Verificación de HMAC en cada mensaje
- ✅ Validación de nonce secuencial (rechaza mensajes antiguos)
- ✅ Timeout de sesión automático
- ✅ Cierre seguro de conexión

---

## Requisitos

### Software
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Dependencias Python
```
Flask==3.0.0
flask-socketio==5.3.5
python-socketio==5.10.0
python-engineio==4.8.0
eventlet==0.33.3
```

### Navegadores Compatibles
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

## Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/yezid-jr/chat-seguro.git
cd chat-seguro
```

### 2. Crear Entorno Virtual (Recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Crear Estructura de Carpetas

```bash
python setup.py
```

Esto creará:
```
templates/
static/
  ├── css/
  └── js/
```

### 5. Colocar Archivos en su Lugar

- `chat.html` → `templates/`
- `style.css` → `static/css/`
- `chat.js` → `static/js/`

---

## Estructura del Proyecto

```
chat-seguro-luciernagas/
│
├── server.py                 # Servidor de chat principal (puerto 65432)
├── web_server.py            # Servidor web Flask (puerto 5000)
├── client.py                # Cliente de terminal
├── requirements.txt         # Dependencias Python
├── setup.py                 # Script para crear estructura
├── get_network_info.py      # Utilidad para obtener IP local
├── test_clients.py          # Simulador de múltiples usuarios
├── README.md                # Este archivo
│
├── templates/
│   └── chat.html           # Interfaz HTML del chat
│
└── static/
    ├── css/
    │   └── style.css       # Estilos del chat
    └── js/
        └── chat.js         # Lógica JavaScript del cliente
```

---

## Uso

### Inicio Rápido

#### 1. Iniciar Servidor de Chat

```bash
python server.py
```

Salida esperada:
```
[+] Servidor de chat grupal escuchando en 0.0.0.0:65432
[+] Los mensajes se reenvían entre clientes
```

#### 2. Iniciar Servidor Web

```bash
python web_server.py
```

Salida esperada:
```
[+] Servidor web iniciando en http://0.0.0.0:5000
[+] Asegúrate de que el servidor de chat esté corriendo en el puerto 65432
```

#### 3. Abrir en el Navegador

```
http://localhost:5000
```

### Cliente de Terminal (Opcional)

```bash
# Cliente local
python client.py

# Cliente remoto
python client.py 192.168.1.100
```

### Comandos Disponibles (Terminal)

- `/exit` - Salir del chat
- `/status` - Ver estado de la conexión
- `/users` - Información de usuarios

---

## Arquitectura

### Diagrama de Componentes

```
┌─────────────────┐
│  Navegador Web  │
│   (Cliente 1)   │
└────────┬────────┘
         │ WebSocket
         │
┌────────▼────────┐      TCP Socket      ┌──────────────┐
│  Flask Server   │◄────────────────────►│ Chat Server  │
│  (Puerto 5000)  │     (Puerto 65432)   │   (Core)     │
└────────▲────────┘                       └──────▲───────┘
         │                                       │
         │ WebSocket                             │ TCP Socket
         │                                       │
┌────────┴────────┐                       ┌──────┴───────┐
│  Navegador Web  │                       │   Terminal   │
│   (Cliente 2)   │                       │  (Cliente 3) │
└─────────────────┘                       └──────────────┘
```

### Flujo de Mensajes

```
1. Usuario escribe mensaje en navegador
2. JavaScript envía vía WebSocket a Flask
3. Flask recibe y lo reenvía al Chat Server (cifrado Vernam)
4. Chat Server valida HMAC y nonce
5. Chat Server hace broadcast a todos los clientes
6. Cada cliente recibe, valida y descifra
7. Mensaje se muestra en interfaz
```

### Clases Principales

#### `SecureChatServer` (server.py)
- Maneja conexiones TCP de múltiples clientes
- Establece sesiones seguras
- Cifra/descifra mensajes con Vernam
- Valida HMAC y nonces
- Hace broadcast de mensajes

#### `ChatClientBridge` (web_server.py)
- Puente entre WebSocket y TCP
- Mantiene una conexión por usuario web
- Traduce mensajes entre protocolos

#### `SecureChatClient` (client.py)
- Cliente para terminal
- Establece sesión segura
- Envía/recibe mensajes cifrados

---

## Testing

### Prueba 1: Múltiples Pestañas del Navegador

```bash
# Terminal 1
python server.py

# Terminal 2
python web_server.py

# Navegador
# Abre 3 pestañas: http://localhost:5000
# Envía mensajes en una pestaña y observa las otras
```

### Prueba 2: Simulador Automático

```bash
# Terminal 1
python server.py

# Terminal 2
python web_server.py

# Terminal 3 - Simula 5 usuarios
python test_clients.py 5
```

### Prueba 3: Cliente Terminal + Web

```bash
# Terminal 1
python server.py

# Terminal 2
python web_server.py

# Terminal 3
python client.py

# Navegador
http://localhost:5000

# Chatea entre ambos clientes
```

### Prueba 4: Red Local (Múltiples Dispositivos)

```bash
# En tu computadora
python get_network_info.py
# Anota la IP mostrada, ej: 192.168.1.100

# Desde tu celular o tablet
# Abre: http://192.168.1.100:5000
```

### Tests Unitarios (Próximamente)

```bash
# Ejecutar tests
python -m pytest tests/

# Con cobertura
python -m pytest --cov=. tests/
```

---

## 🐛 Troubleshooting

### Error: "No se pudo conectar al servidor"

**Causa**: El servidor de chat no está corriendo o no es accesible.

**Solución**:
```bash
# 1. Verifica que server.py esté corriendo
ps aux | grep server.py

# 2. Reinicia el servidor
python server.py

# 3. Verifica el puerto
netstat -an | grep 65432
```

### Error: "Template not found"

**Causa**: Estructura de carpetas incorrecta.

**Solución**:
```bash
# Crear estructura correcta
python setup.py

# Verificar que exista:
# templates/chat.html
ls -la templates/

# static/css/style.css
# static/js/chat.js
ls -la static/css/
ls -la static/js/
```

### Error: "CORS policy" en el navegador

**Causa**: Dominio no permitido en WebSocket.

**Solución** en `web_server.py`:
```python
socketio = SocketIO(app, cors_allowed_origins="*")
# O especifica tu dominio:
socketio = SocketIO(app, cors_allowed_origins="https://tu-dominio.com")
```

### Error: "Address already in use"

**Causa**: El puerto 5000 o 65432 está ocupado.

**Solución**:
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
lsof -ti:65432 | xargs kill -9
```

### Los mensajes no se reciben en tiempo real

**Causa**: WebSocket no se conecta correctamente.

**Solución**:
1. Abre DevTools (F12) en el navegador
2. Ve a la pestaña "Console"
3. Busca errores de WebSocket
4. Verifica que `socket.io.min.js` se cargue correctamente

### Error: "Mensaje corrupto"

**Causa**: HMAC inválido o problema de cifrado.

**Solución**:
1. Verifica que la `master_key` sea la misma en `server.py` y `web_server.py`
2. Reinicia ambos servidores
3. Limpia caché del navegador (Ctrl+Shift+Del)

---

## 🔒 Seguridad en Producción

### ⚠️ IMPORTANTE: Cambios Necesarios

1. **Cambiar la clave maestra**

En `server.py` y `web_server.py`:
```python
# ❌ NO uses esto en producción
master_key = b'Luciernagas_GlobalFinance_2024'

# ✅ Usa una clave fuerte única
master_key = os.urandom(32)  # Guárdala en variable de entorno
```

2. **Usar variables de entorno**

Crea `.env`:
```env
MASTER_KEY=tu_clave_super_secreta_de_32_bytes_en_base64
SECRET_KEY=otra_clave_secreta_para_flask
CHAT_SERVER_HOST=localhost
CHAT_SERVER_PORT=65432
```

Actualiza el código:
```python
from dotenv import load_dotenv
import os
import base64

load_dotenv()

master_key = base64.b64decode(os.getenv('MASTER_KEY'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
```

3. **Habilitar HTTPS**

En producción, SIEMPRE usa HTTPS:
- Railway/Render: Automático ✅
- VPS: Usa Certbot + Let's Encrypt

4. **Límites de tasa (Rate Limiting)**

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/')
@limiter.limit("10/minute")
def index():
    return render_template('chat.html')
```

5. **Validación de entrada**

```python
def sanitize_message(message):
    # Limitar longitud
    if len(message) > 500:
        message = message[:500]
    
    # Eliminar caracteres peligrosos
    message = message.replace('<', '&lt;').replace('>', '&gt;')
    
    return message
```

---

## 📊 Monitoreo y Logs

### Ver logs en producción

```bash
# Railway
railway logs

# Heroku
heroku logs --tail

# VPS
sudo journalctl -u chat-server -f
sudo journalctl -u chat-web -f
```

### Logs importantes a monitorear

- Conexiones/desconexiones de usuarios
- Errores de cifrado/HMAC
- Timeouts de sesión
- Excepciones no manejadas

---

## 🎨 Personalización

### Cambiar colores del tema

En `static/css/style.css`:
```css
/* Gradiente principal */
background: linear-gradient(135deg, #TU_COLOR1 0%, #TU_COLOR2 100%);

/* Ejemplos de paletas */
/* Azul oceánico */
background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);

/* Rosa suave */
background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);

/* Verde natura */
background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
```

### Agregar emojis

En `static/js/chat.js`:
```javascript
function addEmojiPicker() {
    // Agrega tu picker de emojis favorito
    // Ejemplo: emoji-mart, emoji-picker-element, etc.
}
```

### Agregar notificaciones de escritura

```javascript
// Cliente detecta escritura
messageInput.addEventListener('input', () => {
    socket.emit('typing', { username: username });
});

// Servidor reenvía
socket.on('typing', (data) => {
    showTypingIndicator(data.username);
});
```

---

## Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Guías de contribución

- Sigue PEP 8 para código Python
- Documenta funciones con docstrings
- Agrega tests para nuevas features
- Actualiza el README si es necesario

---

## Roadmap

### Versión 1.1
- [ ] Historial de mensajes en base de datos
- [ ] Autenticación con contraseña
- [ ] Salas de chat múltiples
- [ ] Indicador de "escribiendo..."

### Versión 1.2
- [ ] Envío de archivos cifrados
- [ ] Emojis y reacciones
- [ ] Mensajes privados (DM)
- [ ] Notificaciones de escritorio

### Versión 2.0
- [ ] Cifrado end-to-end completo (Signal Protocol)
- [ ] Aplicación móvil (React Native)
- [ ] Llamadas de voz cifradas
- [ ] Videollamadas P2P

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

```
MIT License

Copyright (c) 2024 Chat Seguro Luciérnagas

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Autores

- **Yezid** - *Desarrollo inicial* - [GitHub](https://github.com/yezid-jr)

## Soporte

- **Issues**: [GitHub Issues](https://github.com/yezid-jr/chat-seguro-luciernagas/issues)
- **Discusiones**: [GitHub Discussions](https://github.com/yezid-jr/chat-seguro-luciernagas/discussions)
- **Email**: castrogil202@gmail.com

---

## ¿Te gustó el proyecto?

¡Dale una estrella ⭐ en GitHub si te resultó útil!

---

**Hecho con ❤️ y mucho ☕**