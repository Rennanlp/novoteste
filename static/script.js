async function toggleObservationInput(checkbox) {
    var observationInput = checkbox.parentNode.parentNode.querySelector('.observation-input');
    var numberInput = checkbox.parentNode.parentNode.querySelector('.numb-input');
    observationInput.style.display = checkbox.checked ? 'block' : 'none';
    numberInput.style.display = checkbox.checked ? 'block' : 'none';
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
        var qtd = document.querySelectorAll('.numb-input');

        // Construir os dados do formulário
        var formData = new FormData();
        formData.append('data', data);
        observations.forEach(function(observation, index) {
            formData.append('observations[]', observation.value);
            formData.append('number1[]', qtd[index].value);
        
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

    var maxAttempts = 15; // Número máximo de tentativas
    var attempts = 0;

    // Função para buscar rastreamento
    async function fetchTracking() {
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

                return true; // Retorna sucesso
            } else {
                throw new Error('Não foram encontrados eventos de rastreamento para o número informado.');
            }
        } catch (error) {
            console.error('Erro ao buscar rastreamento:', error);
            return false; // Retorna falha
        }
    }

    // Loop de tentativas
    async function attemptSearch() {
        while (attempts < maxAttempts) {
            attempts++;
            var success = await fetchTracking();
            if (success) {
                return; // Encerra o loop se a busca for bem-sucedida
            }
            await new Promise(resolve => setTimeout(resolve, 1000)); // Aguarda 1 segundo antes de tentar novamente
        }
        // Se exceder o número máximo de tentativas
        resultDiv.removeChild(loadingDiv); // Remove o elemento de loading
        resultDiv.innerHTML = 'Excedido o número máximo de tentativas. Por favor, tente novamente mais tarde.';
    }

    attemptSearch(); // Inicia o loop de tentativas
}

async function removeTask(buttonElement) {
    try {
        const listItem = buttonElement.closest('.checkbox-wrapper');

        // Verifica se encontrou o elemento pai
        if (!listItem) {
            console.error('Elemento pai não encontrado.');
            return;
        }

        const taskIndex = Array.from(listItem.parentNode.children).indexOf(listItem);

        // Certifica que o índice não seja 'null' ou indefinido antes de enviar a solicitação
        if (taskIndex !== null && taskIndex !== undefined) {
            const response = await fetch('/remove_task', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `task_index=${taskIndex}`,
            });

            if (!response.ok) {
                throw new Error('Falha ao remover a tarefa');
            }

            const data = await response.json();

            if (data.status === 'success') {
                // Remove visualmente a tarefa da lista no cliente
                listItem.remove();
                alert('Tarefa removida com sucesso!');
            } else {
                console.error('Falha ao remover a tarefa:', data.message);
                alert('Falha ao remover a tarefa. Por favor, tente novamente.');
            }
        } else {
            console.error('Índice de tarefa inválido:', taskIndex);
            alert('Índice de tarefa inválido. Por favor, recarregue a página e tente novamente.');
        }
    } catch (error) {
        console.error('Erro na requisição AJAX:', error);
        alert('Erro na requisição AJAX. Por favor, tente novamente.');
    }
}

function addTask() {
    var newTaskValue = document.getElementById('task').value.trim();

    if (newTaskValue !== '') {
        $.ajax({
            type: 'POST',
            url: '/add_task',
            data: { task: newTaskValue },
            success: function (response) {
                var taskId = 'task_' + Date.now();
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

                document.querySelector('.list-container ul').appendChild(newTaskElement);
                document.getElementById('task').value = '';
            },
            error: function (error) {
                console.error('Erro ao adicionar tarefa:', error);
            }
        });
    }
}

document.getElementById('saveButton').addEventListener('click', function() {
    // Enviar solicitação para a rota /save_tasks
    fetch('/save_tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
    })
    .then(response => response.json())
    .then(data => {

        console.log(data);
    })
    .catch((error) => {
        console.error('Erro ao salvar tarefas:', error);
    });
});

function enviarDadosParaDashboard() {
    // Obter os dados (tasks, date-input, numb-input, observation-input)
    const tasksData = [...document.querySelectorAll('.list-container input[name="tasks"]:checked')].map(checkbox => checkbox.value);
    const dateInputData = document.getElementById('data').value;
    const numbInputData = [...document.querySelectorAll('.numb-input')].map(input => input.value);
    const observationInputData = [...document.querySelectorAll('.observation-input')].map(input => input.value);

    // Enviar os dados para a rota de dashboard usando AJAX
    fetch('/dashboard', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            tasks: tasksData,
            dateInput: dateInputData,
            numbInput: numbInputData,
            observationInput: observationInputData,
        }),
    })
    .then(response => response.json())
    .then(data => {
        // Manipular a resposta, se necessário
        console.log(data);
    })
    .catch(error => {
        console.error('Erro durante a solicitação AJAX:', error);
    });
}

function addNote() {
    const rawDate = document.getElementById('date').value;
    const notes = document.getElementById('notes').value;
    
    // Formatando a data de aaaa-mm-dd para dd-mm-aaaa
    const parts = rawDate.split("-");
    const formattedDate = parts[2] + "-" + parts[1] + "-" + parts[0];

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/add_note', true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            // Atualize apenas a seção de anotações na página
            document.getElementById('savedNotes').innerHTML = xhr.responseText;
        }
    };
    
    // Enviando a data formatada e as notas para o servidor
    xhr.send(`date=${formattedDate}&notes=${notes}`);

    showModal();

    // Após alguns segundos, ocultar a janela flutuante de sucesso
    setTimeout(hideModal, 3000); // Tempo em milissegundos (neste caso, a janela será ocultada após 3 segundos)
}

function getNotes() {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', '/get_notes', true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            // Atualize a seção de anotações na página
            document.getElementById('savedNotes').innerHTML = xhr.responseText;
        }
    };
    xhr.send();
}

function hideModal() {
    var modal = document.getElementById('modal');
    modal.style.display = 'none';
}

function showModal() {
    var modal = document.getElementById('modal');
    modal.style.display = 'block';

    // Fechar a modal quando o botão 'x' for clicado
    var closeButton = document.querySelector('.close');
    closeButton.addEventListener('click', function() {
        hideModal(); // Chama a função para fechar a modal
    });

    // Fechar a modal quando clicar fora dela
    window.addEventListener('click', function(event) {
        if (event.target == modal) {
            hideModal(); // Chama a função para fechar a modal
        }
    });

    // Adicionar temporizador para fechar automaticamente após 3 segundos (3000 milissegundos)
    setTimeout(function() {
        hideModal(); // Chama a função para fechar a modal
    }, 3000);

}

// Função para mostrar a animação de check e exibir a modal
function showSuccessCheck() {
    var modalContent = document.querySelector('.modal-content');
    modalContent.innerHTML = '<span class="checkmark">&#10003;</span><p id="success-message">Anotações salvas com sucesso!</p>';
    var checkmark = document.querySelector('.checkmark');
    checkmark.style.display = 'inline-block'; // Exibe o checkmark

    showModal(); // Chama a função para exibir a modal

    console.log('closeButton:', closeButton);
    console.log('modalContent:', modalContent);
}

