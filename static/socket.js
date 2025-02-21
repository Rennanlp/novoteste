// Definir a URL base do Socket.IO
var baseSocketUrl = 'https://removedorrp.onrender.com';

// Conectar ao Socket.IO diretamente à URL base com timeout e reconexão
var socket = io.connect(baseSocketUrl, {
    transports: ['websocket', 'polling'],
    timeout: 10000  // Timeout de 10 segundos
});

// Função para criar uma notificação visual
function showNotification(message) {
    var notification = document.createElement('div');
    notification.classList.add('notification');
    notification.innerText = message;

    document.body.appendChild(notification);

    setTimeout(function() {
        notification.remove();
    }, 5000);  // A notificação desaparece após 5 segundos
}

// Função para reproduzir um som de notificação
function playNotificationSound() {
    var audio = new Audio('static/notification.mp3');  // Caminho para o arquivo de som
    audio.play();
}

// Função para exibir o ponto de notificação no ícone do Trecco
function showNotificationDot() {
    var notificationDot = document.getElementById('notification-dot');
    if (notificationDot) {
        notificationDot.style.display = 'inline-block';  // Exibe o ponto de notificação
    }
}

// Função para esconder o ponto de notificação
function hideNotificationDot() {
    var notificationDot = document.getElementById('notification-dot');
    if (notificationDot) {
        notificationDot.style.display = 'none';  // Esconde o ponto de notificação
    }
}

// Escutar as notificações para o usuário
socket.on('notification', function(data) {
    console.log('Notificação recebida:', data);  // Debug
    showNotification(data.message);  // Exibe a notificação visual
    playNotificationSound();         // Reproduz o som de notificação
    showNotificationDot();           // Exibe o ponto de notificação no ícone

    // Armazenar no localStorage que há notificações pendentes
    localStorage.setItem('task_assigned', 'true');
});

// Quando a página carregar, verificar se há notificações pendentes
window.onload = function() {
    // Se houver notificações pendentes no localStorage, exibir o ponto vermelho
    if (localStorage.getItem('task_assigned') === 'true') {
        showNotificationDot();
    }

    // Se o usuário estiver na página de login, não fazer nada
    if (window.location.pathname === '/login') {
        return;
    }

    // Se o usuário acessar a página Trecco, remover a notificação
    if (window.location.pathname === '/trecco') {
        hideNotificationDot();
        localStorage.removeItem('task_assigned');  // Limpa o status de notificação
    }
};

// Verificar se a conexão foi bem-sucedida
socket.on('connect', function() {
    console.log('Conectado ao Socket.IO');
});

// Caso ocorra um erro na conexão
socket.on('connect_error', function(error) {
    console.log('Erro na conexão do Socket.IO: ', error);
    alert('Erro ao tentar conectar ao servidor. Tente novamente mais tarde.');
});

// Detectar reconexão
socket.on('reconnect', function(attempt) {
    console.log(`Reconectado ao Socket.IO após ${attempt} tentativas.`);
});

// Caso haja um erro ao tentar reconectar
socket.on('reconnect_error', function(error) {
    console.log('Erro ao tentar reconectar: ', error);
});

// Caso a reconexão falhe
socket.on('reconnect_failed', function() {
    console.log('Falha ao reconectar ao Socket.IO.');
    alert('Falha ao reconectar ao servidor. Por favor, tente mais tarde.');
});
