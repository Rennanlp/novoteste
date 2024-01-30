from flask import Flask, render_template, request, send_file, redirect, session, url_for
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

tasks = []

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

def generate_excel(tasks):
    output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'lista_de_tarefas.xlsx')

    # Criar um arquivo Excel
    workbook = xlsxwriter.Workbook(output_filepath)
    worksheet = workbook.add_worksheet()

    # Escrever os cabeçalhos
    worksheet.write(0, 0, 'Tarefa')

    # Escrever as tarefas
    for i, task in enumerate(tasks, start=1):
        worksheet.write(i, 0, task)

    # Fechar o arquivo Excel
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

            # Especificar o delimitador usado no arquivo CSV (por exemplo, ';')
            delimiter = ';'

            # Processar o conteúdo do arquivo CSV
            with open(filepath, 'r', encoding='utf-8') as input_file:
                reader = csv.reader(input_file, delimiter=delimiter)
                rows = [list(map(lambda x: unidecode(x) if x else x, row)) for row in reader]

            # Criar um arquivo de saída para o novo CSV
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
    return render_template('form.html', tasks=tasks)

@app.route('/add_task', methods=['POST'])
def add_task():
    new_task = request.form.get('task')
    tasks.append(new_task)
    return redirect(url_for('task_f'))

@app.route('/download_excel', methods=['POST'])
def download_excel():
    # Gerar o arquivo Excel
    excel_filepath = generate_excel(tasks)

    # Enviar o arquivo para download
    return send_file(excel_filepath, as_attachment=True)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
