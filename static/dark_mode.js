
const darkModeToggle = document.getElementById('dark-mode-toggle');

// Definir o estado inicial com base na preferência armazenada
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
    darkModeToggle.checked = true;
}

// Alternar modo escuro quando o switch for clicado
darkModeToggle.addEventListener('change', function () {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
});
