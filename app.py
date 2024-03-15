# app.py
from flask import Flask, render_template, request, send_file, redirect, session, url_for, jsonify, g, render_template_string
from werkzeug.utils import secure_filename
from unidecode import unidecode
import os
import csv
from datetime import datetime
from functools import wraps
import xlsxwriter
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from collections import defaultdict
from jinja2 import Environment



app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or b'_5#y2L"F4Q8z\n\xec]/'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
app.config['STATIC_FOLDER'] = 'static'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)
CORS(app)
migrate = Migrate(app, db)


def format_date(value, format='%d/%m/%Y'):
    # Verifica se o valor já é uma string, se for, não faz nada
    if isinstance(value, str):
        return value
    # Se o valor não for uma string, assume que é um objeto datetime e formata conforme o formato especificado
    return value.strftime(format)

app.jinja_env.filters['date'] = format_date

user_tasks = {}
user_quantities = {}
saved_data = {}
dashboard_data = {}

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

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # Alteração no formato da data
    content = db.Column(db.Text, nullable=False)

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

def generate_excel(username, tasks):
    print("User tasks:", user_tasks)
    
    # Obter os dados do formulário
    data = request.form.get('data')
    observations = request.form.getlist('observations[]')
    qtd = request.form.getlist('number1[]')

    print("Tasks:", tasks)
    print("Data:", data)
    print("Observations:", observations)
    print("Quantidades:", qtd)

    output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'lista_de_tarefas.xlsx')

    # Gerar arquivo Excel
    workbook = xlsxwriter.Workbook(output_filepath)
    worksheet = workbook.add_worksheet()

    # cabeçalhos
    worksheet.write(0, 0, 'Tarefa')
    worksheet.write(0, 1, 'Data')
    worksheet.write(0, 2, 'Pedidos no Dia' )
    worksheet.write(0, 3, 'Observação')

    # Escreve as tarefas
    for i, task in enumerate(tasks, start=1):
        worksheet.write(i, 0, task)
        worksheet.write(i, 1, data)
        worksheet.write(i, 2, qtd[i - 1] if i <= len(qtd) else '')
        if i <= len(observations):
            worksheet.write(i, 3, observations[i - 1])


    workbook.close()

    return output_filepath

@app.route('/')
@login_required
def index():
    username = user_database.get(session.get('username', ''), {}).get('name', 'Convidado')
    print("Username in session:", session.get('username'))
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
@login_required
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
@login_required
def download_excel():
    username = session['username']
    tasks = user_tasks.get(username, [])
    
    # Gera o arquivo Excel usando o nome de usuário da sessão e as tarefas
    excel_filepath = generate_excel(username, tasks)

    # Envia o arquivo para download
    return send_file(excel_filepath, as_attachment=True)

@app.route('/remove_task', methods=['POST'])
@login_required
def remove_task():
    username = session['username']

    try:
        task_index = int(request.form.get('task_index'))

        if 0 <= task_index < len(user_tasks.get(username, [])):
            removed_task = user_tasks[username].pop(task_index)
            return jsonify({'status': 'success', 'removed_task': removed_task})
        else:
            return jsonify({'status': 'error', 'message': 'Índice de tarefa inválido'})
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Índice de tarefa inválido'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/clear_tasks', methods=['POST'])
@login_required
def clear_tasks():
    username = session['username']

    if username in user_tasks:
        user_tasks[username] = []

    return jsonify({'status': 'success'})

@app.route('/rastreamento', methods=['GET', 'POST'])
@login_required
def rastreio():
    return render_template('sro.html')


import matplotlib.pyplot as plt
import pandas as pd

# ...

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('teste.html')

@app.route('/add_note', methods=['POST'])
@login_required
def add_note():
    username = session['username']
    note_date_str = request.form.get('date')
    note_content = request.form.get('notes').replace('\n', '<br>')

    if note_date_str:
        # Convertendo a data de "dd-mm-aaaa" para "aaaa-mm-dd"
        note_date = datetime.strptime(note_date_str, '%d-%m-%Y').strftime('%Y-%m-%d')

        new_note = Note(username=username, date=note_date, content=note_content)
        db.session.add(new_note)
        db.session.commit()

        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Data inválida'})

@app.route('/get_notes', methods=['GET'])
@login_required
def get_notes():
    username = session['username']
    notes = Note.query.filter_by(username=username).order_by(Note.date).all()

    grouped_notes = defaultdict(list)
    for note in notes:
        if note.date:  # Verifica se a data não está vazia
            try:
                # Convertendo a data de volta para o formato d/m/Y
                note_date = datetime.strptime(note.date, '%Y-%m-%d')
                # Adicionando o dia da semana na data formatada
                note_date_formatted = note_date.strftime('%d/%m/%Y') + ' - ' + note_date.strftime('%A')
                grouped_notes[note_date_formatted].append(note)
            except ValueError:
                # Lidar com datas inválidas, se necessário
                pass

    return render_template('notes.html', grouped_notes=grouped_notes)

@app.route('/remove_note', methods=['POST'])
@login_required
def remove_note():
    note_id = request.form.get('note_id')
    username = session['username']

    # Verifica se a nota pertence ao usuário atual antes de removê-la
    note = Note.query.filter_by(id=note_id, username=username).first()

    if note:
        db.session.delete(note)
        db.session.commit()
        # Recarrega a página após a remoção bem-sucedida
        return redirect(url_for('get_notes'))
    else:
        return jsonify({'status': 'error', 'message': 'Nota não encontrada ou você não tem permissão para removê-la.'})
    
@app.route('/clear_notes', methods=['POST'])
@login_required
def clear_notes():
    username = session['username']

    # Remove todas as notas do usuário atual do banco de dados
    num_deleted = Note.query.filter_by(username=username).delete()
    db.session.commit()

    return redirect(url_for('get_notes'))


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
