function toggleObservationInput(checkbox) {
    var observationInput = checkbox.parentNode.parentNode.querySelector('.observation-input');

    if (checkbox.checked) {
        observationInput.style.display = 'block';
    } else {
        observationInput.style.display = 'none';
        observationInput.value = ''; // Limpar o conteúdo quando desmarcar
    }
}

function clearTaskList() {
    // Desmarcar todas as checkboxes
    document.querySelectorAll('.checkbox-input input:checked').forEach(function (checkbox) {
        checkbox.checked = false;
    });

    // Limpar todas as entradas de observação
    document.querySelectorAll('.observation-input').forEach(function (observationInput) {
        observationInput.value = '';
    });

    // Remover todos os itens da lista (incluindo os dinâmicos)
    document.querySelectorAll('.checkbox-wrapper').forEach(function (item) {
        item.parentNode.removeChild(item);
    });
}

// Função para exportar a lista para um arquivo Excel e iniciar o download
function downloadExcelFile() {
    var tasks = [];
    var observations = [];
    var dates = [];

    // Coletar tarefas, observações e datas
    document.querySelectorAll('.checkbox-input input:checked').forEach(function (checkbox) {
        var task = checkbox.nextSibling.textContent;
        var observation = checkbox.parentNode.parentNode.querySelector('.observation-input').value;
        var date = new Date().toLocaleDateString(); // Obtendo a data atual no formato local (você pode personalizar conforme necessário)
        tasks.push(task);
        observations.push(observation);
        dates.push(date);
    });

    // Criar um objeto de workbook do xlsx
    var wb = XLSX.utils.book_new();
    var ws = XLSX.utils.aoa_to_sheet([['Tarefa', 'Observação', 'Data']].concat(tasks.map(function (task, index) {
        return [task, observations[index], dates[index]];
    })));

    XLSX.utils.book_append_sheet(wb, ws, 'Lista de Tarefas');

    // Convertendo o workbook em um blob
    var blob = XLSX.write(wb, { bookType: 'xlsx', type: 'blob' });

    // Criar um URL do blob
    var url = URL.createObjectURL(blob);

    // Criar um link de download
    var a = document.createElement('a');
    a.href = url;
    a.download = 'lista_de_tarefas.xlsx';

    // Adicionar o link ao corpo da página e clicar automaticamente nele
    document.body.appendChild(a);
    a.click();

    // Remover o link após o download
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function changePage() {
    var pageSelector = document.getElementById('pageSelector');
    var selectedPage = pageSelector.options[pageSelector.selectedIndex].value;
    window.location.href = selectedPage;
}
