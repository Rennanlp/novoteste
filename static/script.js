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
        // Atualizar a interface
        if (data.status === 'success') {
            // recarregar a página
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
        // Obter os dados do formulário
        var data = document.getElementById('data').value;
        var observations = document.querySelectorAll('.observation-input');

        // Construir os dados do formulário
        var formData = new FormData();
        formData.append('data', data);
        observations.forEach(function(observation, index) {
            formData.append('observations[]', observation.value);
        });

        // Enviar uma requisição AJAX para o endpoint de download
        fetch('/download_excel', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Falha no download do arquivo Excel');
            }
            return response.blob();
        })
        .then(blob => {
            // Criar um link para o download e clicar nele
            var url = window.URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'ListaDeTarefas.xlsx';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Erro no download do arquivo Excel:', error);
            alert('Erro no download do arquivo Excel. Por favor, tente novamente.');
        });
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