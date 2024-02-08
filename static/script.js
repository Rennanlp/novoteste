async function toggleObservationInput(checkbox) {
    var observationInput = checkbox.parentNode.parentNode.querySelector('.observation-input');
    observationInput.style.display = checkbox.checked ? 'block' : 'none';
    if (!checkbox.checked) {
        observationInput.value = ''; // Limpar o conteúdo quando desmarcar
    }
}

async function clearTaskList() {
    try {
        const response = await fetch('/clear_tasks', {
            method: 'POST',
        });

        if (!response.ok) {
            throw new Error('Falha na limpeza da lista de tarefas');
        }

        const data = await response.json();

        if (data.status === 'success') {
            // recarregar a página
            location.reload();
        } else {
            console.error('Falha ao limpar a lista de tarefas');
            alert('Falha ao limpar a lista de tarefas. Por favor, tente novamente.');
        }
    } catch (error) {
        console.error('Erro na requisição AJAX:', error);
        alert('Erro na requisição AJAX. Por favor, tente novamente.');
    }
}

async function downloadExcelFile() {
    try {
        // Obter os dados do formulário
        var data = document.getElementById('data').value;
        var observations = document.querySelectorAll('.observation-input');

        // Construir os dados do formulário
        var formData = new FormData();
        formData.append('data', data);
        observations.forEach(function (observation, index) {
            formData.append('observations[]', observation.value);
        });

        // Enviar uma requisição AJAX para o endpoint de download
        const response = await fetch('/download_excel', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Falha no download do arquivo Excel');
        }

        const blob = await response.blob();

        // Criar um link para o download e clicar nele
        var url = window.URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'ListaDeTarefas.xlsx';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Erro no download do arquivo Excel:', error);
        alert('Erro no download do arquivo Excel. Por favor, tente novamente.');
    }
}

function changePage() {
    var pageSelector = document.getElementById('pageSelector');
    var selectedPage = pageSelector.options[pageSelector.selectedIndex].value;
    window.location.href = selectedPage;
}

async function searchTracking() {
    var trackingNumber = document.getElementById('trackingNumber').value;
    var resultDiv = document.getElementById('result');
    var loadingDiv = document.createElement('div'); // Novo elemento para mostrar o loading

    // Adiciona um estilo ao elemento de loading
    loadingDiv.textContent = 'Buscando informações de rastreamento...';

    // Adiciona o elemento de loading à div de resultado
    resultDiv.innerHTML = '';  // Limpa o conteúdo anterior
    resultDiv.appendChild(loadingDiv);

    // Adiciona um tempo de espera simulando o loading (por exemplo, 2 segundos)
    var loadingTime = 2000; // 2 segundos
    setTimeout(async function () {
        try {
            var requestOptions = {
                method: 'GET',
                redirect: 'follow'
            };

            var apiUrl = `https://api.linketrack.com/track/json?user=teste&token=1abcd00b2731640e886fb41a8a9671ad1434c599dbaa0a0de9a5aa619f29a83f&codigo=${trackingNumber}`;

            const response = await fetch(apiUrl, requestOptions);
            const data = await response.json();

            // Verifica se há eventos de rastreamento
            if (data.eventos && data.eventos.length > 0) {
                // Constrói a mensagem com base em todos os eventos
                var message = 'Detalhes do Rastreamento:<br>';

                data.eventos.forEach(evento => {
                    message += `<strong>Data:</strong> ${evento.data}<br>`;
                    message += `<strong>Hora:</strong> ${evento.hora}<br>`;
                    message += `<strong>Status:</strong> ${evento.status}<br>`;
                    message += `<strong>Local:</strong> ${evento.local}<br><br>`;
                });

                // Remove o elemento de loading
                resultDiv.removeChild(loadingDiv);

                // Atualiza a div de resultado com a mensagem construída
                resultDiv.innerHTML = message;
            } else {
                resultDiv.removeChild(loadingDiv); // Remove o elemento de loading
                resultDiv.innerHTML = 'Não foram encontrados eventos de rastreamento para o número informado.';
            }
        } catch (error) {
            console.error('Erro ao buscar rastreamento:', error);
            resultDiv.removeChild(loadingDiv); // Remove o elemento de loading
            resultDiv.innerHTML = 'Erro ao buscar rastreamento. Por favor, tente novamente.';
        }
    }, loadingTime);
}
function removeTask(buttonElement) {
    // Obtém o elemento pai li da tarefa a ser removida
    var listItem = buttonElement.closest('.checkbox-wrapper');

    // Remove o elemento li da lista
    listItem.remove();
}
function addTask() {
    // Obtenha o valor da nova tarefa do input
    var newTaskValue = document.getElementById('task').value;

    // Verifique se o valor não está vazio antes de adicionar a nova tarefa
    if (newTaskValue.trim() !== '') {
        // Crie um identificador único para a nova tarefa
        var taskId = 'task_' + Date.now();

        // Crie um novo elemento li para a nova tarefa
        var newTaskElement = document.createElement('li');
        newTaskElement.classList.add('checkbox-wrapper');
        newTaskElement.innerHTML = `
            <div class="checkbox-input">
                <input type="checkbox" id="${taskId}" name="tasks" value="${newTaskValue}" onchange="toggleObservationInput(this)">
                <label for="${taskId}"></label>
            </div>
            <span>${newTaskValue}</span>
            <input type="text" class="observation-input" name="observations[]" placeholder="Observações">
            <button type="button" class="remove-task" onclick="removeTask(this)">
            <svg class="remove-svgIcon" viewBox="0 0 448 512">
                <path d="M135.2 17.7L128 32H32C14.3 32 0 46.3 0 64S14.3 96 32 96H416c17.7 0 32-14.3 32-32s-14.3-32-32-32H320l-7.2-14.3C307.4 6.8 296.3 0 284.2 0H163.8c-12.1 0-23.2 6.8-28.6 17.7zM416 128H32L53.2 467c1.6 25.3 22.6 45 47.9 45H346.9c25.3 0 46.3-19.7 47.9-45L416 128z"></path>
              </svg>
</button>
        `;

        // Adicione o novo elemento li à lista de tarefas
        document.querySelector('.list-container ul').appendChild(newTaskElement);

        // Limpe o valor do input após adicionar a tarefa
        document.getElementById('task').value = '';
    }
}
