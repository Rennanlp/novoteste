function toggleObservationInput(checkbox) {
    var observationInput = checkbox.parentNode.parentNode.querySelector('.observation-input');
    observationInput.style.display = checkbox.checked ? 'block' : 'none';
    if (!checkbox.checked) {
        observationInput.value = ''; // Limpar o conteúdo quando desmarcar
    }
}

function clearTaskList() {
    // Enviar uma requisição AJAX para o endpoint de limpar tarefas
    fetch('/clear_tasks', {
        method: 'POST',
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Falha na limpeza da lista de tarefas');
        }
        return response.json();
    })
    .then(data => {
        // Atualizar a interface ou realizar outras ações necessárias
        if (data.status === 'success') {
            // Por exemplo, recarregar a página
            location.reload();
        } else {
            console.error('Falha ao limpar a lista de tarefas');
            alert('Falha ao limpar a lista de tarefas. Por favor, tente novamente.');
        }
    })
    .catch(error => {
        console.error('Erro na requisição AJAX:', error);
        alert('Erro na requisição AJAX. Por favor, tente novamente.');
    });
}

function downloadExcelFile() {
    try {
        // Adicionar um timestamp à URL para evitar o caching
        var timestamp = new Date().getTime();
        var url = '/download_excel?timestamp=' + timestamp;

        // Criar um link para o download e clicar nele
        var a = document.createElement('a');
        a.href = url;
        a.download = 'ListaDeTarefas.xlsx';
        a.click();
    } catch (error) {
        console.error('Erro ao exportar para o Excel:', error);
        alert('Erro ao exportar para o Excel. Por favor, tente novamente.');
    }
}

function changePage() {
    var pageSelector = document.getElementById('pageSelector');
    var selectedPage = pageSelector.options[pageSelector.selectedIndex].value;
    window.location.href = selectedPage;
}
