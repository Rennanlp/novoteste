# app.py
from flask import Flask, render_template, request, send_file, redirect, session, url_for, jsonify
from werkzeug.utils import secure_filename
from unidecode import unidecode
import os
import csv
from datetime import datetime
from functools import wraps
import xlsxwriter


app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or b'_5#y2L"F4Q8z\n\xec]/'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
app.config['STATIC_FOLDER'] = 'static'

user_tasks = {}

# banco de usuários
user_database = {
    'conexao.premium': {
        'password': 'senha123',
        'name': 'Conexão Premium'
    },
    'Renan10': {
        'password': '162593',
        'name': 'Renan'
    },
    'Thais10': {
        'password': 'arthur08',
        'name': 'Gerente'
    },
    'Diogo10': {
        'password': '15222431',
        'name': 'Duzac07'
    },
    'Keyse10': {
        'password': 'keyse321',
        'name': 'Keyse'
    },
    'Nicoli10': {
        'password': 'ririserelepe',
        'name': 'Nic'
    },
    'Ingrid10': {
        'password': '135781',
        'name': 'Ingrid'
    },
    'Eduarda': {
        'password': 'eduarda10',
        'name': 'Duda'
    }
}

# verificar se o usuário está logado
def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped_view

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_excel(username):
    tasks = user_tasks.get(username, [])

    # Obter os dados do formulário
    data = request.form.get('data')
    observations = request.form.getlist('observations[]')

    output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'lista_de_tarefas.xlsx')

    # Criar um arquivo Excel
    workbook = xlsxwriter.Workbook(output_filepath)
    worksheet = workbook.add_worksheet()

    # Escreve os cabeçalhos
    worksheet.write(0, 0, 'Tarefa')
    worksheet.write(0, 1, 'Data')
    worksheet.write(0, 2, 'Observação')

    # Escreve os dados das tarefas
    for i, task in enumerate(tasks, start=1):
        worksheet.write(i, 0, task)
        worksheet.write(i, 1, data)
        if i <= len(observations):
            worksheet.write(i, 2, observations[i - 1])

    # Fecha o arquivo Excel
    workbook.close()

    return output_filepath

@app.route('/')
@login_required
def index():
    username = user_database.get(session.get('username', ''), {}).get('name', 'Convidado')
    return render_template('index.html', username=username)

# Página de login
@app.route('/login')
def login1():
    if 'username' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

# autenticar o login
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')  # pegar o campo 'username'
    password = request.form.get('senha')

    if username in user_database and user_database[username]['password'] == password:
        session['username'] = username  # armazenar o nome de usuário na sessão
        return redirect(url_for('index'))
    else:
        return render_template('login.html', error='Usuário ou senha incorretos, tente novamente.')

@app.route('/remove_accent', methods=['POST'])
def remove_accent():
    if 'file' not in request.files:
        return "Nenhum arquivo enviado."

    file = request.files['file']

    if file.filename == '':
        return "Nenhum arquivo selecionado."

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Adiciona a seguinte linha para obter o encoding do formulário
            encoding = request.form.get('encoding', 'utf-8')

            # Tenta abrir o arquivo CSV com o encoding fornecido
            try:
                with open(filepath, 'r', encoding=encoding) as input_file:
                    delimiter = ';'  # Especificar o delimitador usado no arquivo CSV
                    reader = csv.reader(input_file, delimiter=delimiter)
                    rows = [list(map(lambda x: unidecode(x) if x else x, row)) for row in reader]
            except UnicodeDecodeError:
                # Se ocorrer um erro de decodificação, tenta abrir com 'latin-1'
                with open(filepath, 'r', encoding='latin-1') as input_file:
                    delimiter = ';'  # Especifica o delimitador usado no arquivo
                    reader = csv.reader(input_file, delimiter=delimiter)
                    rows = [list(map(lambda x: unidecode(x) if x else x, row)) for row in reader]

            # Cria um arquivo de saída para o novo CSV
            output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'Arquivo_Ajustado_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
            with open(output_filepath, 'w', encoding='utf-8', newline='') as output_file:
                writer = csv.writer(output_file, delimiter=delimiter)
                writer.writerows(rows)

            return send_file(output_filepath, download_name=filename, as_attachment=True)

        except Exception as e:
            return "Erro durante o processamento do arquivo: {}".format(str(e))

    return "Tipo de arquivo não permitido."


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/task')
@login_required
def task_f():
    username = session['username']
    user_task_list = user_tasks.get(username, [])
    return render_template('form.html', tasks=user_task_list)

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    new_task = request.form.get('task')
    username = session['username']

    if username not in user_tasks:
        user_tasks[username] = []

    user_tasks[username].append(new_task)
    return redirect(url_for('task_f'))

@app.route('/download_excel', methods=['GET','POST'])
def download_excel():
    username = session['username']

    # Gera o arquivo Excel usando o nome de usuário da sessão
    excel_filepath = generate_excel(username)

    # Envia o arquivo para download
    return send_file(excel_filepath, as_attachment=True)

@app.route('/clear_tasks', methods=['POST'])
@login_required
def clear_tasks():
    username = session['username']

    if username in user_tasks:
        user_tasks[username] = []

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
