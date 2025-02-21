var baseSocketUrl = 'https://removedorrp.onrender.com';

var socket = io.connect(baseSocketUrl, {
    transports: ['websocket', 'polling'],
    timeout: 10000
});

function showNotification(message) {
    var notification = document.createElement('div');
    notification.classList.add('notification');
    notification.innerText = message;

    document.body.appendChild(notification);

    setTimeout(function() {
        notification.remove();
    }, 5000);
}

function playNotificationSound() {
    var audio = new Audio('static/notification.mp3');
    audio.play();
}

function showNotificationDot() {
    var notificationDot = document.getElementById('notification-dot');
    if (notificationDot) {
        notificationDot.style.display = 'inline-block';
    }
}

function hideNotificationDot() {
    var notificationDot = document.getElementById('notification-dot');
    if (notificationDot) {
        notificationDot.style.display = 'none';
    }
}

socket.on('notification', function(data) {
    showNotification(data.message);
    playNotificationSound();
    showNotificationDot();

    localStorage.setItem('task_assigned', 'true');
});

window.onload = function() {
    if (localStorage.getItem('task_assigned') === 'true') {
        showNotificationDot();
    }

    if (window.location.pathname === '/login') {
        return;
    }

    if (window.location.pathname === '/trecco') {
        hideNotificationDot();
        localStorage.removeItem('task_assigned');
    }
};

socket.on('connect', function() {
    console.log('Conectado ao Socket.IO');
});

socket.on('connect_error', function(error) {
    console.log('Erro na conexão do Socket.IO: ', error);
    alert('Erro ao tentar conectar ao servidor. Tente novamente mais tarde.');
});

socket.on('reconnect', function(attempt) {
    console.log(`Reconectado ao Socket.IO após ${attempt} tentativas.`);
});

socket.on('reconnect_error', function(error) {
    console.log('Erro ao tentar reconectar: ', error);
});

socket.on('reconnect_failed', function() {
    console.log('Falha ao reconectar ao Socket.IO.');
    alert('Falha ao reconectar ao servidor. Por favor, tente mais tarde.');
});
