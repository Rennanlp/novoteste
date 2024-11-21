# app.py
from flask import Flask, render_template, request, send_file, redirect, session, url_for, jsonify, g, render_template_string, json, make_response, flash
from unidecode import unidecode
import os
import csv
from datetime import datetime, timedelta
from functools import wraps
import xlsxwriter
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from collections import defaultdict
from jinja2 import Environment
import requests
import sqlite3
from werkzeug.utils import secure_filename
import io
import pandas as pd
from io import BytesIO
import asyncio
import aiohttp
from clientes import criar_banco_dados, inserir_dados_da_planilha, obter_responsaveis_e_empresas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Frame, PageTemplate
from reportlab.pdfgen import canvas
import io
import textwrap
from flask_mail import Mail, Message
from openpyxl import Workbook
from sqlalchemy import or_
import pytz

# CONFUGURAÇÕES FLASK #
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or b'_5#y2L"F4Q8z\n\xec]/'
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['UPLOAD_FOLDER1'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv', }
app.config['STATIC_FOLDER'] = 'static'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['MAX_CONTENT_LENGTH'] = 48 * 1024 * 1024
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_BINDS'] = {
    'database1': 'sqlite:///database1.db'
}
db = SQLAlchemy(app)
CORS(app)
migrate = Migrate(app, db)

# CONFIGURAÇÕES MAIL #
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'apikey' 
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = 'conexaopremium26@gmail.com'


mail = Mail(app)


def format_date(value, format='%d/%m/%Y'):

    if isinstance(value, str):
        return value

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
    },
    'Felipe': {
    'password': 'felipe@10',
    'name': 'Felipe'
    },
    'Gabriela': {
    'password': 'gabriela@10',
    'name': 'Gabriela'
    },
    'Kymberli': {
    'password': 'kym@10',
    'name': 'Kym'
    },
    'Ana Paula': {
    'password': 'ana@10',
    'name': 'Ana'
    },
    'Juliana': {
    'password': 'juliana@10',
    'name': 'Juliana'
    }
    
}

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)

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
    
    # Obtem os dados do formulário
    data = request.form.get('data')
    observations = request.form.getlist('observations[]')
    qtd = request.form.getlist('number1[]')

    print("Tasks:", tasks)
    print("Data:", data)
    print("Observations:", observations)
    print("Quantidades:", qtd)

    output_filepath = os.path.join(app.config['UPLOAD_FOLDER1'], 'lista_de_tarefas.xlsx')

    # Gera arquivo Excel
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

def process_csv(file):
    conn = sqlite3.connect('clientes.db')
    c = conn.cursor()
    
    try:
        csv_reader = csv.reader(io.TextIOWrapper(file, encoding='latin-1'), delimiter=';')
    except Exception as e:
        print("Erro ao tentar abrir o arquivo CSV:", e)
        return

    next(csv_reader, None)

    for row in csv_reader:
        if len(row) >= 2 and all(row[:2]):
            id, cliente, token = row[0], row[1], row[2]
            c.execute("INSERT INTO clientes (id, cliente, token) VALUES (?, ?, ?)", (id, cliente, token))
        else:
            print("Ignorando linha do arquivo CSV com formato inválido:", row)

    conn.commit()
    conn.close()

def criar_tabela():
    conn = sqlite3.connect('clientes.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
                        id INTEGER PRIMARY KEY,
                        cliente TEXT,
                        token TEXT
                    )''')
    conn.commit()
    conn.close()

criar_tabela()

def obter_token_por_cliente(nome_cliente):
    conn = sqlite3.connect('clientes.db')
    cursor = conn.cursor()

    cursor.execute("SELECT token FROM clientes WHERE LOWER(cliente) = LOWER(?)", (nome_cliente,))
    resultado = cursor.fetchone()

    conn.close()

    if resultado:
        return resultado[0]
    else:
        return None

@app.route('/removedor')
@login_required
def removedor():
    username = user_database.get(session.get('username', ''), {}).get('name', 'Convidado')
    print("Username in session:", session.get('username'))
    return render_template('index.html', username=username)

@app.route('/login')
def login1():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# autenticar o login
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('senha')

    if username in user_database and user_database[username]['password'] == password:
        session['username'] = username 
        return redirect(url_for('dashboard'))
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

            encoding = request.form.get('encoding', 'utf-8')

            # Tenta abrir o arquivo CSV com o encoding fornecido
            try:
                with open(filepath, 'r', encoding=encoding) as input_file:
                    delimiter = ';'
                    reader = csv.reader(input_file, delimiter=delimiter)
                    rows = [list(map(lambda x: unidecode(x) if x else x, row)) for row in reader]
            except UnicodeDecodeError:
                # Se ocorrer um erro de decodificação, tentar abrir com 'latin-1'
                with open(filepath, 'r', encoding='latin-1') as input_file:
                    delimiter = ';'
                    reader = csv.reader(input_file, delimiter=delimiter)
                    rows = [list(map(lambda x: unidecode(x) if x else x, row)) for row in reader]

            # Criar um arquivo de saída para o novo CSV
            output_filepath = os.path.join(app.config['UPLOAD_FOLDER1'], f'Arquivo_Ajustado_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
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


# @app.route('/dashboard', methods=['GET', 'POST'])
# @login_required
# def dashboard():
#     return render_template('teste.html')

@app.route('/add_note', methods=['POST'])
@login_required
def add_note():
    username = session['username']
    note_date_str = request.form.get('date')
    note_content = request.form.get('notes').replace('\n', '<br>')

    if note_date_str:
        
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
        if note.date:
            try:
                # Convertendo a data de volta para o formato d/m/Y
                note_date = datetime.strptime(note.date, '%Y-%m-%d')

                note_date_formatted = note_date.strftime('%d/%m/%Y') + ' - ' + note_date.strftime('%A')
                grouped_notes[note_date_formatted].append(note)
            except ValueError:

                pass

    return render_template('notes.html', grouped_notes=grouped_notes)

@app.route('/remove_note', methods=['POST'])
@login_required
def remove_note():
    note_id = request.form.get('note_id')
    username = session['username']

    note = Note.query.filter_by(id=note_id, username=username).first()

    if note:
        db.session.delete(note)
        db.session.commit()

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

@app.route('/cadastro')
@login_required
def cadastro():
    return render_template('cadastro.html')

@app.route('/pesquisar', methods=['POST'])
@login_required
def pesquisar():
    nome_cliente = request.form['cliente']
    data_inicial = datetime.strptime(request.form['data_inicial'], '%Y-%m-%d').strftime('%d/%m/%Y')
    data_final = datetime.strptime(request.form['data_final'], '%Y-%m-%d').strftime('%d/%m/%Y')

    conn = sqlite3.connect('clientes.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE cliente = ?", (nome_cliente,))
    resultado = cursor.fetchone()

    if resultado:
        token = resultado[2]
        conn.close()

        url = "https://api.boxlink.com.br/preenvio/consultar-periodo"
        payload = json.dumps({
            "dataInicial": request.form['data_inicial'],
            "dataFinal": request.form['data_final'],
            "preenvioCancelado": True,
            "envioExpedido": True
        })
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        data = json.loads(response.text)
        chave_seller = sum('chaveSeller' in d for d in data)
        preEnvio_cancelado = sum(d['preenvioCancelado'] for d in data if 'preenvioCancelado' in d)
        envio_expedido = sum(d['envioExpedido'] for d in data if 'envioExpedido' in d)

        resultado_final = chave_seller - envio_expedido - preEnvio_cancelado

        mensagem = "{}\n\n de {} a {}:\n\n {} etiqueta(s) aguardando impressão".format(nome_cliente, data_inicial, data_final, resultado_final)
    else:
        mensagem = "Cliente não encontrado ou token não disponível."

    print("Mensagem retornada:", mensagem)

    return jsonify({'mensagem': mensagem})

@app.route('/adicionar', methods=['POST'])
@login_required
def adicionar():
    id = request.form['id']
    cliente = request.form['cliente']
    token = request.form['token']

    conn = sqlite3.connect('clientes.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO clientes (id, cliente, token)
                    VALUES (?, ?, ?)''', (id, cliente, token))
    conn.commit()
    conn.close()

    return redirect(url_for('cadastro'))

@app.route('/upload_csv', methods=['POST'])
@login_required
def upload_csv():
    if request.method == 'POST':

        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '' or not file.filename.endswith('.csv'):
            return redirect(request.url)
        
        try:
            process_csv(file)
            mensagem = "Dados adicionados com sucesso."
            return redirect(url_for('cadastro', mensagem=mensagem))
        except Exception as e:
            print(e)
            mensagem = "Ocorreu um erro ao processar o arquivo CSV."
            return redirect(url_for('cadastro', mensagem=mensagem))

def obter_dados_da_api(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        return None 

async def consulta_api_box_async(token, data_inicio, data_fim):
    nova_data_inicio = (datetime.strptime(data_inicio, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    url_api_box = "https://api.boxlink.com.br/preenvio/consultar-periodo"
    payload = {
        "dataInicial": nova_data_inicio,
        "dataFinal": data_fim,
        "preenvioCancelado": True,
        "envioExpedido": True
    }
    headers = {'Authorization': 'Bearer ' + token}
    
    for attempt in range(3): 
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url_api_box, json=payload, headers=headers, timeout=30) as response:
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        data = await response.json()
                        
                        if isinstance(data, list) and all(isinstance(d, dict) for d in data):
                            chave_seller = sum('chaveSeller' in d for d in data)
                            preEnvio_cancelado = sum(d.get('preenvioCancelado', False) for d in data)
                            envio_expedido = sum(d.get('envioExpedido', False) for d in data)
                            resultado = chave_seller - envio_expedido - preEnvio_cancelado
                            return resultado
                        else:
                            print(f"Erro: 'data' retornado pela API não está no formato esperado. Data: {data}")
                            return None
                    else:
                        text = await response.text()
                        raise aiohttp.client_exceptions.ContentTypeError(
                            response.request_info,
                            response.history,
                            status=response.status,
                            message=f'Attempt to decode JSON with unexpected mimetype: {content_type}',
                            headers=response.headers,
                        )
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt == 2:
                raise e
            await asyncio.sleep(2)

async def consulta_api_box(tokens, data_inicio, data_fim):
    tasks = []
    for token in tokens:
        task = consulta_api_box_async(token, data_inicio, data_fim)
        tasks.append(task)
    return await asyncio.gather(*tasks)

@app.route('/lista_completa')
async def lista_completa():
    # print("Request args:", request.args)
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')

    if not data_inicio or not data_fim:
        return render_template('testeapi.html')
    
    try:
        data_inicio_formatted = datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%Y%m%d')
        data_fim_formatted = datetime.strptime(data_fim, '%Y-%m-%d').strftime('%Y%m%d')
    except ValueError:
        return "Formato de data inválido. Por favor, insira as datas no formato correto."

    try:
        url_api_crm = f"https://ap5tntnr6b.execute-api.us-east-1.amazonaws.com/api/transcrmc/{data_inicio_formatted}/{data_fim_formatted}"
        dados_api_crm = obter_dados_da_api(url_api_crm)
        # print("Dados retornados pela API CRM:", dados_api_crm)

        if dados_api_crm is None:
            return "Erro ao obter dados da primeira API"
        
        if not isinstance(dados_api_crm, list):
            # print(f"Erro: dados_api_crm deveria ser uma lista, mas é {type(dados_api_crm)}")
            return "Erro ao obter dados da primeira API"

        search_query = request.args.get('search', '')
        if search_query:
            dados_api_crm = [
                item for item in dados_api_crm if isinstance(item, dict) and search_query.lower() in item.get('Cliente', '').lower()
            ]

        dados_formatados = [(item['Id_Cliente'], item['Cliente'], item['Pedidos'], item['Token']) for item in dados_api_crm]
        # print("Dados formatados:", dados_formatados)

        tokens = [item['Token'] for item in dados_api_crm]
        try:
            resultado_final = await consulta_api_box(tokens, data_inicio, data_fim)
        except aiohttp.client_exceptions.ContentTypeError as e:
            print("Erro ao obter dados da segunda API:", e)
            return "Erro ao obter dados da segunda API"

        return render_template('testeapi.html', dados=dados_formatados, data_inicio=data_inicio, data_fim=data_fim, resultado_final=resultado_final)

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return "Erro interno no servidor"


@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.form.get('data')

        dados = eval(data)
        resultado_final = [row[3] for row in dados]

        df = pd.DataFrame(dados, columns=['Id_Cliente', 'Cliente', 'Pedidos CRM', 'Pedidos BOX'])

        output = BytesIO()

        df.to_excel(output, index=False)

        output.seek(0)

        response = make_response(send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
        response.headers["Content-Disposition"] = "attachment; filename=dados.xlsx"
        return response
    except Exception as e:
        return f"Erro ao processar o download: {str(e)}"

@app.route('/carregar_lista_responsaveis', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'Nenhum arquivo encontrado'
        
        file = request.files['file']
        
        if file.filename == '' or not file.filename.endswith('.xlsx'):
            return 'Por favor, selecione um arquivo Excel (.xlsx)'
        
        try:
            from io import BytesIO
            import pandas as pd
            
            criar_banco_dados()
            
            df = pd.read_excel(BytesIO(file.read()))
            
            inserir_dados_da_planilha(df)
            
            return 'Dados enviados com sucesso'
        except Exception as e:
            return f'Ocorreu um erro ao processar o arquivo: {str(e)}'
    
    return render_template('upload.html')

@app.route('/up_clientes')
@login_required
def up_clientes():
    return render_template('upload.html')

class Trello(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    responsavel = db.Column(db.String(100), nullable=False)
    CD = db.Column(db.String(100), nullable=False)
    link = db.Column(db.String(200), nullable=False)

class Links(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)

@app.route('/links_uteis')
@login_required
def links():
    
    conn = sqlite3.connect('database1.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT nome, responsavel, CD, link FROM trello")
    clientes = cursor.fetchall()
    
    cursor.execute("SELECT titulo, url FROM links")
    outros_links = cursor.fetchall()
    
    conn.close()
    
    return render_template('links_uteis.html', clientes=clientes, outros_links=outros_links)

def connect_db():
    return sqlite3.connect('database1.db')

@app.route('/inserir_link', methods=['POST'])
@login_required
def inserir_link():
    if request.method == 'POST':
        titulo = request.form['titulo']
        url = request.form['url']

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO links (titulo, url) VALUES (?, ?)", (titulo, url))
        conn.commit()
        conn.close()
        return redirect('/links_uteis')

@app.route('/inserir_trello', methods=['POST'])
@login_required
def inserir_trello():
    if request.method == 'POST':
        nome = request.form['nome']
        responsavel = request.form['responsavel']
        CD = request.form['CD']
        link = request.form['link']
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO trello (nome, responsavel, CD, link) VALUES (?, ?, ?, ?)", (nome, responsavel, CD, link))
        conn.commit()
        conn.close()
        return redirect('/links_uteis')
    

@app.route('/buscacep', methods=['GET', 'POST'])
def buscacep():
    if request.method == 'POST':
        uf = request.form.get('uf')
        cidade = request.form.get('cidade')
        bairro = request.form.get('bairro')
        logradouro = request.form.get('logradouro')
        
        api_url = f"https://viacep.com.br/ws/{uf}/{cidade}/{logradouro}/json/"
        
        try:
            response = requests.get(api_url)
            response.raise_for_status()  # Verifica se ocorreu algum erro HTTP
            
            data = response.json()
            if data:  # Verificar se data não está vazio
                return render_template('buscacep.html', data=data)
            else:
                error = "Nenhum Resultado encontrado. Verifique os dados e tente novamente."
                return render_template('buscacep.html', error=error)
        
        except requests.exceptions.ConnectionError:
            error = "Erro de conexão. Verifique sua rede e tente novamente."
            return render_template('buscacep.html', error=error)
        
        except requests.exceptions.Timeout:
            error = "A requisição para a API expirou. Tente novamente mais tarde."
            return render_template('buscacep.html', error=error)
        
        except requests.exceptions.RequestException as e:
            error = f"Erro ao fazer a requisição: {e}"
            return render_template('buscacep.html', error=error)

    return render_template('buscacep.html')

@app.route('/buscacep_cep')
def bcep():
    return render_template('buscacep_cep.html')


# ROTAS E DEF FATURA EM PDF

# Função para quebrar texto
def wrap_text(text, width):
    return '\n'.join(textwrap.wrap(text, width=width))

# Função para converter DataFrame para lista de listas
def dataframe_to_list(dataframe):
    l = []
    lista = [dataframe.columns.values.tolist()] + dataframe.fillna('').values.tolist()
    del lista[0]
    l.append(["Objeto", "Postagem", "Valor", "Destinatário", "Cidade", "Observação"])
    for i in lista:
        try:
            observacao = i[11] if pd.notnull(i[11]) else ''
            l.append([
                i[0],
                i[3].strftime("%d/%m/%Y") if isinstance(i[3], datetime) else str(i[3]),
                ("R$ " + '%.2f' % i[4]).replace(".", ",") if isinstance(i[4], (int, float)) else str(i[4]),
                i[5],
                i[6],
                observacao
            ])
        except Exception as e:
            print(f"Erro ao processar linha: {i}, erro: {e}")
            continue
    return l

# Função para desenhar o cabeçalho
def header(canvas, doc, pini, pfin, cliente, estado):
    page_width, page_height = letter
    margin = 50
    canvas.saveState()
    canvas.setFont('Helvetica', 13)
    canvas.drawString(210, page_height - margin - 40, 'Fatura Resumida de Serviços Prestados')
    canvas.drawImage("static/correios.png", margin, page_height - margin - 40, width=120, height=25)
    canvas.setFont('Helvetica', 9)
    current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    canvas.drawString(margin, page_height - margin - 75, f'Período de: {pini} até: {pfin} - Data da emissão: {current_date}')
    canvas.drawString(margin, page_height - margin - 85, f'Cliente: {cliente}')
    
    if estado == 'SC':
        canvas.drawString(margin, page_height - margin - 95, 'PALHOÇA - SC - PACHECOS - RUA VIKINGS 30 - 88134-878')
    elif estado == 'SP':
        canvas.drawString(margin, page_height - margin - 95, 'INDAIATUBA - SP - CENTRO - RUA ONZE DE JUNHO 1318 - 13330-972')
    elif estado == 'ES':
        canvas.drawString(margin, page_height - margin - 95, 'VITORIA - ES - CENTRO - RUA ENGENHEIRO PINTO PACCA 25 LJ D CAIXA POSTAL 10010  - 29010-973')
        
    canvas.setTitle(f"Relatórios Correios {pini} - {pfin}")
    canvas.restoreState()
    
# Função para desenhar o rodapé
def footer(canvas, doc):
    page_width, page_height = letter
    margin = 16
    
    canvas.saveState()
    
    rect_x = margin
    rect_y = margin
    rect_width = page_width - 2 * margin
    rect_height = 50
    radius = 10

    canvas.roundRect(rect_x, rect_y, rect_width, rect_height, radius, stroke=1, fill=0)

    canvas.setFont('Helvetica-Bold', 8.5)
    text = "A Empresa Brasileira de Correios e Telégrafos é imune a Imposto de Renda conforme sentença judicial - Recurso Extraordinário STF\n601.392/PR amparada no art.150, alínea a da CF/88 e no Decreto-lei 509/1969."
    text_lines = text.split('\n')
    
    text_x = rect_x + 10
    text_y = rect_y + rect_height - 15

    for line in text_lines:
        canvas.drawString(text_x, text_y, line)
        text_y -= 10 

    canvas.setFont('Helvetica-Oblique', 6)
    footer_text = "Para pagamento do Boleto junto ao seu Banco, se necessário utilize o CNPJ Matriz dos Correios: 34.028.316/0001-03 no campo Beneficiário, porexigência da CIP (Câmara interbancária de Pagamento)."
    
    text_y -= 20
    canvas.drawString(margin, text_y, footer_text)
    
    canvas.restoreState()

# Classe customizada para contar as páginas e adicionar o rodapé na última
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page_number, page in enumerate(self.pages, start=1):
            self.__dict__.update(page)
            # Adicionar o rodapé apenas na última página
            if page_number == page_count:
                footer(self, None)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

def process_excel_to_pdf(file, pini, pfin, cliente, estado, nomearquivo):
    df = pd.read_excel(file, sheet_name="Planilha1")

    width = 20

    # Aplicar wrap_text apenas a colunas de texto
    df = df.applymap(lambda x: wrap_text(x, width) if isinstance(x, str) else x)

    data_list = dataframe_to_list(df)

    pdf_buffer = io.BytesIO()
    pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    elements = []

    table = Table(data_list, colWidths=[(612 - 2 * 50) / 6] * 6)
    bg_color = colors.Color(68 / 255, 114 / 255, 196 / 255)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), bg_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
        ('TOPPADDING', (0, 0), (-1, 0), 3),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0, colors.white)
    ])
    
    last_row = len(data_list) - 1
    style.add('BACKGROUND', (0, last_row), (-1, last_row), bg_color)
    style.add('TEXTCOLOR', (0, last_row), (-1, last_row), colors.white)

    table.setStyle(style)
    elements.append(table)

    # Adicionando o cabeçalho e o rodapé
    frame = Frame(pdf.leftMargin, pdf.bottomMargin, pdf.width, pdf.height - 2 * 50, id='normal')
    template = PageTemplate(id='test', frames=[frame], 
                            onPage=lambda canvas, doc: header(canvas, doc, pini, pfin, cliente, estado))
    pdf.addPageTemplates([template])

    # Construindo o PDF
    pdf.build(elements, canvasmaker=NumberedCanvas)

    # Retornando o buffer do PDF
    pdf_buffer.seek(0)
    return pdf_buffer

@app.route('/gerar_pdf', methods=['GET', 'POST'])
@login_required
def gerar_pdf():
    if request.method == 'POST':
        # Recebendo dados do formulário
        file = request.files['file']
        pini = request.form['pini']
        pfin = request.form['pfin']
        cliente = request.form['cliente']
        estado = request.form['estado']  # Captura o estado selecionado (SC ou SP)
        nomearquivo = request.form['nomearquivo']

        # Gerando o PDF
        pdf_buffer = process_excel_to_pdf(file, pini, pfin, cliente, estado, nomearquivo)

        # Enviando o PDF gerado para o cliente
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"{nomearquivo}.pdf",
            mimetype='application/pdf'
        )

    # Se for GET, apenas renderiza o formulário
    return render_template('gerar_pdf.html')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def normalizar_string(s):
    return s.upper().strip()

def somar_observacoes(observacao):
    produtos = {}
    if pd.isna(observacao):
        return produtos 

    observacao = str(observacao).strip()
    items = observacao.split('|')
    for item in items:
        item = item.strip()
        if 'x' in item:
            partes = item.split('x', 1)
            if len(partes) == 2:
                quantidade_str = partes[0].strip()
                produto = normalizar_string(partes[1].strip())
                
                try:
                    quantidade = int(quantidade_str)
                except ValueError:
                    quantidade = 1
                    
                if "EBOOK" not in produto:
                    if produto in produtos:
                        produtos[produto] += quantidade
                    else:
                        produtos[produto] = quantidade

    return produtos

@app.route('/somar_produtos')
def upload_file():
    return render_template('upload.html')

df_resultado = None

@app.route('/analisar', methods=['POST'])
def analisar():
    global df_resultado

    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file:
        df = pd.read_csv(file, delimiter=';', encoding='ISO-8859-1')

        print("DataFrame Original:")
        print(df.head())

        df_observacoes = df['Observação'].apply(somar_observacoes)
        df_expanded = pd.json_normalize(df_observacoes)
        df = pd.concat([df, df_expanded], axis=1)

        df = df.drop(columns=['Observação'])

        print("DataFrame Após Expansão:")
        print(df.head())

        df_resultado = df.groupby('Data').sum().reset_index()

        print("DataFrame Após Agrupamento:")
        print(df_resultado.head())

        for coluna in df_resultado.columns:
            if df_resultado[coluna].dtype == 'float64':
                df_resultado[coluna] = df_resultado[coluna].fillna(0).astype(int)

        df_resultado['Data'] = pd.to_datetime(df_resultado['Data'], errors='coerce', format='%d/%m/%Y')
        df_resultado = df_resultado.sort_values(by='Data')

        df_resultado['Data'] = df_resultado['Data'].dt.strftime('%d/%m/%y')
        
        df_resultado = df_resultado.loc[:, ~df_resultado.columns.str.contains('^Unnamed')]

        print("DataFrame Após Remoção de Colunas 'Unnamed':")
        print(df_resultado.head())

        total_row = df_resultado.drop(columns=['Data']).sum()
        total_row['Data'] = 'Total Geral' 

        df_resultado.loc[len(df_resultado)] = total_row

        html_table = df_resultado.to_html(classes='table table-striped', index=False).strip()

        total_geral = df_resultado.drop(columns=['Data']).sum().sum()

        return render_template('resultado.html', 
                               tables=[html_table], 
                               titles=df_resultado.columns.values,
                               total_geral=total_geral)
        
@app.route('/download_xlsx')
def download_xlsx():
    global df_resultado

    if df_resultado is None:
        return redirect('/')

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_resultado.to_excel(writer, index=False, sheet_name='Resultado')

    output.seek(0)
    return send_file(output, as_attachment=True, download_name='resultado.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


def processar_cancelamento(lines):
    url = "https://api.boxlink.com.br/v2/pre-envio/cancelar-com-rastreador"
    headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJqb25hc2dhcmNpYTY2NkBnbWFpbC5jb20iLCJVU0VSX0RFVEFJTFMiOnsidXNlcklkIjoxNTgzLCJtYXRyaXpJZCI6MTcsImZyYW5xdWlhSWQiOjksImNsaWVudGVJZCI6MjI1fSwiZXhwIjo1OTk1NzM4ODAwfQ.SEjKpWAkD_j5oosJ1RaSQq2JmMeXHhc459FqzJtxXc0',
        'User-Agent': 'Apidog/1.0.0 (https://apidog.com)',
        'Content-Type': 'application/json'
    }

    async def cancelar_rastreadores():
        async with aiohttp.ClientSession() as session:
            tasks = []
            for l in lines:
                payload = {
                    "rastreadorTms": l.strip(),
                    "motivo": "Solicitado pela Logistica"
                }
                task = asyncio.create_task(session.put(url, headers=headers, json=payload))
                tasks.append(task)
            responses = await asyncio.gather(*tasks)
            return responses

    return asyncio.run(cancelar_rastreadores())

@app.route('/cancelamento_etiquetas', methods=['GET', 'POST'])
@login_required
def cancelamento():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('cancelamento.html', message='Nenhum arquivo foi enviado')
        
        file = request.files['file']
        
        if file.filename == '':
            return render_template('cancelamento.html', message='Nenhum arquivo selecionado')
        
        if file and file.filename.endswith('.csv'):

            lines = file.read().decode('utf-8').splitlines()
            lines = lines[1:] 

            processar_cancelamento(lines)

            return render_template('cancelamento.html', message='Cancelamento realizado com sucesso')
        
        return render_template('cancelamento.html', message='Arquivo inválido. Por favor, revise a extensão (csv).')

    return render_template('cancelamento.html')

import httpx

async def fetch_news():
    api_key = "98e1265378d2abc81736b6495d5a0fe3"
    url = "https://gnews.io/api/v4/top-headlines"
    
    params = {
        "country": "br",
        "apikey": api_key,
        "lang": "pt",
        "max": 5
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
        if response.status_code == 200:
            articles = response.json().get("articles", [])
            return [
                {
                    "title": article["title"],
                    "description": article.get("description", "Sem descrição disponível"),
                    "url": article["url"],
                    "image": article.get("image", "path/to/placeholder.jpg")  # Adiciona o campo de imagem com um placeholder se não houver URL
                }
                for article in articles
            ]
        else:
            print("Erro ao buscar notícias:", response.status_code, response.text)
            return []

async def fetch_weather(city="Charqueadas", lat=None, lon=None):
    api_key = "eb8a5f8b0ace4c7fe4622f6deadcd5d0"
    url = "https://api.openweathermap.org/data/2.5/weather"
    
    params = {
        "appid": api_key,
        "units": "metric"
    }
    
    if lat and lon:
        params["lat"] = lat
        params["lon"] = lon
    else:
        params["q"] = city
    
    weather_translation = {
        "clear sky": "céu Limpo",
        "few clouds": "Poucas Nuvens",
        "scattered clouds": "Nuvens Dispersas",
        "broken clouds": "Nuvens Fragmentadas",
        "shower rain": "Chuva Leve",
        "rain": "Chuva",
        "thunderstorm": "Tempestade",
        "snow": "Neve",
        "mist": "Neblina",
        "overcast clouds": "Nublado",
        "moderate rain": "Chuva moderada",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
        if response.status_code == 200:
            weather_data = response.json()
            description = weather_data['weather'][0]['description']
            translated_description = weather_translation.get(description, description)
            weather_data['weather'][0]['description'] = translated_description
            
            deg = weather_data['wind']['deg']
            directions = ['Norte', 'Nordeste', 'Leste', 'Sudeste', 'Sul', 'Sudoeste', 'Oeste', 'Noroeste']
            weather_data['wind_direction'] = directions[int((deg + 22.5) % 360 / 45)]
            
            return weather_data
        else:
            print("Erro ao buscar o clima:", response.status_code, response.text)
            return None

@app.route("/", methods=["GET", "POST"])
@login_required
def dashboard():
    lat = None
    lon = None
    if request.method == "POST":
        data = request.get_json()
        lat = data.get("lat")
        lon = data.get("lon")
        
        weather = asyncio.run(fetch_weather(lat=lat, lon=lon))
        return jsonify(weather) if weather else jsonify({"error": "Erro ao buscar clima"}), 500
    
    weather = asyncio.run(fetch_weather())
    news = asyncio.run(fetch_news())
    username = user_database.get(session.get('username', ''), {}).get('name', 'Convidado')
    
    return render_template("dashboard.html", weather=weather, news=news, username=username)

from google.oauth2.service_account import Credentials
import gspread

# Configurações
ESCOPOS = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
PLANILHA_ID = "13Ivq0l0ueMB6GjO0xr6umLx7qHMvPJRAomjgxf3CunE"
CREDENCIAIS_JSON = os.getenv("GOOGLE_CREDENTIALS")  # Variável de ambiente para o JSON compactado

# Cabeçalho personalizado
CABECALHO_PERSONALIZADO = [
    "Data",
    "Nome da Empresa",
    "Email",
    "Nome dos Produtos",
    "Quando inicar os envios",
    "Pedidos em atraso",
    "Kits",
    "Envie Fotos",
    "Acessos Plat. Vendas",
    "Acessos Plat. NFs",  # Mantido no cabeçalho
    "CNPJ",
    "Fornecedor"
]


async def acessar_planilha_forms():
    """Função assíncrona para acessar a planilha e formatar os dados."""
    try:
        # Salvar credenciais em um arquivo temporário
        if not CREDENCIAIS_JSON:
            raise Exception("Credenciais do Google não foram configuradas.")
        
        caminho_temp = "/tmp/credentials.json"  # Caminho temporário no servidor
        with open(caminho_temp, "w") as cred_file:
            cred_file.write(CREDENCIAIS_JSON)

        # Autenticação e acesso à planilha
        credenciais = Credentials.from_service_account_file(caminho_temp, scopes=ESCOPOS)
        cliente = gspread.authorize(credenciais)
        planilha = cliente.open_by_key(PLANILHA_ID)
        aba_forms = planilha.worksheet("Respostas ao formulário 1")

        # Obter dados da planilha
        dados_raw = aba_forms.get_all_records(empty2zero=False)
        colunas_planilha = aba_forms.row_values(1)

        # Filtrar e formatar os dados
        dados_filtrados = [registro for registro in dados_raw if any(registro.values())]
        dados_formatados = []

        for registro in dados_filtrados:
            novo_registro = {}
            for i, coluna in enumerate(colunas_planilha):
                if coluna == "8 - Por gentileza nos encaminhe imagens dos produtos. (WHATSAPP)":
                    continue  # Ignora esta coluna específica
                chave = CABECALHO_PERSONALIZADO[i] if i < len(CABECALHO_PERSONALIZADO) else coluna
                novo_registro[chave] = registro.get(coluna, "")
            dados_formatados.append(novo_registro)

        return dados_formatados

    except gspread.exceptions.WorksheetNotFound:
        return {"erro": "A aba especificada não foi encontrada."}
    except Exception as e:
        return {"erro": f"Erro inesperado: {str(e)}"}


@app.route('/dados-forms')
@login_required
def exibir_dados():
    """Rota para exibir os dados da planilha."""
    dados = asyncio.run(acessar_planilha_forms())
    if "erro" in dados:
        return jsonify(dados)
    return render_template('dados_forms.html', dados=dados)

ALLOWED_EXTENSIONS1 = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file1(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS1

class Reverso(db.Model):
    __tablename__ = 'reverso'
    
    id = db.Column(db.Integer, primary_key=True)
    remetente = db.Column(db.String(100), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id', ondelete='SET NULL'), nullable=True)  # Mudando para nullable=True
    cod_rastreio = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    imagem = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship('Cliente', backref=db.backref('reversos', lazy=True, passive_deletes=True))
    
    def __repr__(self):
        return f'<Reverso {self.remetente} - {self.cod_rastreio}>'

class Cliente(db.Model):
    __tablename__ = 'cliente'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<Cliente {self.nome} - {self.email}>'

from flask_paginate import Pagination

@app.route('/reversos', methods=['GET'])
@login_required
def reversos():
    query = request.args.get('q', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    filters = []

    if query:
        filters.append(
            or_(
                Cliente.nome.ilike(f'%{query}%'),
                Reverso.remetente.ilike(f'%{query}%')
            )
        )

    if start_date:
        filters.append(Reverso.criado_em >= datetime.strptime(start_date, '%Y-%m-%d'))

    if end_date:
        filters.append(Reverso.criado_em <= datetime.strptime(end_date, '%Y-%m-%d'))

    reversos_query = Reverso.query.join(Cliente).filter(*filters).add_columns(
        Reverso.id,
        Cliente.nome.label('cliente'),
        Reverso.cod_rastreio.label('codigo'),
        Cliente.email.label('email'),
        Reverso.criado_em.label('data'),
        Reverso.remetente.label('remetente'),
        Reverso.descricao.label('descricao'),
        Reverso.imagem.label('imagem')
    )

    reversos = reversos_query.paginate(page=page, per_page=per_page, error_out=False)
    pagination = Pagination(page=page, total=reversos.total, per_page=per_page, record_name='reversos')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('partials/reversos_list.html', reversos=reversos.items)

    return render_template('listar_reversos.html', 
                           reversos=reversos.items, 
                           pagination=pagination, 
                           query=query,
                           start_date=start_date,
                           end_date=end_date)

@app.route('/reversos/exportar', methods=['GET'])
@login_required
def exportar_reversos():
    query = request.args.get('q', '')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
    end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

    filters = []
    if query:
        filters.append(
            (Cliente.nome.contains(query) | Reverso.remetente.contains(query))
        )
    if start_date:
        filters.append(Reverso.criado_em >= start_date)
    if end_date:
        filters.append(Reverso.criado_em <= end_date)

    reversos_query = Reverso.query.join(Cliente).filter(*filters).add_columns(
        Cliente.nome.label('cliente'),
        Reverso.cod_rastreio.label('codigo'),
        Cliente.email.label('email'),
        Reverso.criado_em.label('data'),
        Reverso.remetente.label('remetente'),
        Reverso.descricao.label('descricao')
    ).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Reversos"
    
    ws.append(['Cliente', 'Codigo', 'Email', 'Data', 'Remetente', 'Descrição'])

    for reverso in reversos_query:
        ws.append([
            reverso.cliente,
            reverso.codigo,
            reverso.email,
            reverso.data.strftime('%d/%m/%Y'), 
            reverso.remetente,
            reverso.descricao
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    today = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"Reversos-{today}.xlsx"

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return response

from flask import flash, redirect, url_for

br_tz = pytz.timezone('America/Sao_Paulo')

@app.before_request
def before_request():
    g.timezone = br_tz

@app.route('/reversos/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_reverso():
    if request.method == 'POST':
        remetente = request.form['remetente']
        cliente_id = request.form['cliente'] 
        cod_rastreio = request.form['cod_rastreio']
        descricao = request.form['descricao']
        imagem = request.files['imagem'] if 'imagem' in request.files else None

        agora = datetime.now(pytz.utc).astimezone(g.timezone)

        if imagem and allowed_file1(imagem.filename):
            filename = secure_filename(imagem.filename) 
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename) 
            imagem.save(save_path) 
            imagem_path = f"images/{filename}" 
        else:
            imagem_path = None

        cliente = Cliente.query.get(cliente_id)

        novo_reverso = Reverso(
            remetente=remetente,
            cliente=cliente, 
            cod_rastreio=cod_rastreio,
            descricao=descricao,
            imagem=imagem_path,
            criado_em=agora
        )

        db.session.add(novo_reverso)
        db.session.commit()

        try:
            msg = Message(
                subject="Logistica Reversa Recebida",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[cliente.email],
                body=f"""
                Olá {cliente.nome},

                Recebemos uma devolução de Logística Reversa com os seguintes detalhes:
                - Remetente: {remetente}
                - Código de Rastreio: {cod_rastreio}
                - Descrição: {descricao}

                Atenciosamente,
                Equipe Conexão Premium
                """
            )

            if imagem_path:
                with open(os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(imagem_path)), 'rb') as img:
                    msg.attach(
                        filename=os.path.basename(imagem_path),
                        content_type='image/jpg',
                        data=img.read()
                    )

            mail.send(msg)
            flash("E-mail enviado com sucesso!", "success")

        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")
            flash(f"Erro ao enviar o e-mail: {str(e)}", "danger")

        return redirect(url_for('adicionar_reverso'))

    clientes = Cliente.query.all()
    return render_template('adicionar_reverso.html', clientes=clientes)

@app.route('/reversos/delete/<int:id>', methods=['GET'])
@login_required
def deletar_reverso(id):
    reverso = Reverso.query.get(id)

    if reverso:
        if reverso.imagem:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], reverso.imagem))
            except FileNotFoundError:
                pass

        db.session.delete(reverso)
        db.session.commit()

    return redirect(url_for('reversos'))
    
@app.route('/cadastro_cliente', methods=['GET', 'POST'])
@login_required
def cadastro_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        
        if Cliente.query.filter_by(email=email).first():
            return "Este email já está cadastrado. Tente outro."
        
        novo_cliente = Cliente(nome=nome, email=email)
        db.session.add(novo_cliente)
        db.session.commit()
        
        return redirect(url_for('clientes')) 
    
    return render_template('clientes_reverso.html')

@app.route('/clientes')
@login_required
def clientes():
    clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)

@app.route('/excluir_cliente/<int:id>', methods=['POST'])
@login_required
def excluir_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    
    Reverso.query.filter_by(cliente_id=id).delete()
    
    db.session.delete(cliente)
    db.session.commit()
    
    return redirect(url_for('clientes'))

@app.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        cliente.nome = request.form['nome']
        cliente.email = request.form['email']
        
        if Cliente.query.filter(Cliente.email == cliente.email, Cliente.id != id).first():
            return "Este email já está em uso por outro cliente. Tente outro."
        
        db.session.commit()
        return redirect(url_for('clientes'))
    
    return render_template('editar_cliente.html', cliente=cliente)


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
