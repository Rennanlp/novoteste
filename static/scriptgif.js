window.addEventListener('load', function() {
    const tempoMinimoCarregamento = 3000;
    
    setTimeout(function() {
        document.getElementById('loading').style.visibility = 'hidden';
    }, tempoMinimoCarregamento);
});