// // Conectar ao Socket.IO quando a página for carregada
// var socket = io.connect('http://' + document.domain + ':' + location.port);

// // Função para criar uma notificação visual
// function showNotification(message) {
//     var notification = document.createElement('div');
//     notification.classList.add('notification');
//     notification.innerText = message;

//     document.body.appendChild(notification);

//     setTimeout(function() {
//         notification.remove();
//     }, 5000);  // A notificação desaparece após 5 segundos
// }

// // Função para reproduzir um som de notificação
// function playNotificationSound() {
//     var audio = new Audio('static/notification.mp3');  // Caminho para o arquivo de som
//     audio.play();
// }

// // Função para exibir o ponto de notificação no ícone do Trecco
// function showNotificationDot() {
//     var notificationDot = document.getElementById('notification-dot');
//     if (notificationDot) {
//         notificationDot.style.display = 'inline-block';  // Exibe o ponto de notificação
//     }
// }

// // Função para esconder o ponto de notificação
// function hideNotificationDot() {
//     var notificationDot = document.getElementById('notification-dot');
//     if (notificationDot) {
//         notificationDot.style.display = 'none';  // Esconde o ponto de notificação
//     }
// }

// // Escutar as notificações para o usuário
// socket.on('notification', function(data) {
//     showNotification(data.message);
//     playNotificationSound();
//     showNotificationDot();

//     // Armazenar no localStorage que há notificações pendentes
//     localStorage.setItem('task_assigned', 'true');
// });

// // Quando a página carregar, verificar se há notificações pendentes
// window.onload = function() {
//     // Se houver notificações pendentes no localStorage, exibir o ponto vermelho
//     if (localStorage.getItem('task_assigned') === 'true') {
//         showNotificationDot();
//     }

//     // Se o usuário estiver na página de login, não fazer nada
//     if (window.location.pathname === '/login') {
//         return;
//     }

//     // Se o usuário acessar a página Trecco, remover a notificação
//     if (window.location.pathname === '/trecco') {
//         hideNotificationDot();
//         localStorage.removeItem('task_assigned');  // Limpa o status de notificação
//     }
// };
