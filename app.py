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
import io
import textwrap

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or b'_5#y2L"F4Q8z\n\xec]/'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
app.config['STATIC_FOLDER'] = 'static'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_BINDS'] = {
    'database1': 'sqlite:///database1.db'
}
db = SQLAlchemy(app)
CORS(app)
migrate = Migrate(app, db)


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
    'Bernardo': {
    'password': 'bernardo@10',
    'name': 'Bernardo'
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

    output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'lista_de_tarefas.xlsx')

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

@app.route('/')
@login_required
def index():
    username = user_database.get(session.get('username', ''), {}).get('name', 'Convidado')
    print("Username in session:", session.get('username'))
    return render_template('index.html', username=username)

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
        print("Erro ao fazer a requisição:", e)
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
    async with aiohttp.ClientSession() as session:
        async with session.post(url_api_box, json=payload, headers={'Authorization': 'Bearer ' + token}) as response:
            data = await response.json()
            chave_seller = sum('chaveSeller' in d for d in data)
            preEnvio_cancelado = sum(d.get('preenvioCancelado', False) for d in data)
            envio_expedido = sum(d.get('envioExpedido', False) for d in data)
            resultado = chave_seller - envio_expedido - preEnvio_cancelado
            return resultado

async def consulta_api_box(tokens, data_inicio, data_fim):
    tasks = []
    for token in tokens:
        task = consulta_api_box_async(token, data_inicio, data_fim)
        tasks.append(task)
    return await asyncio.gather(*tasks)

@app.route('/lista_completa')
async def lista_completa():
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')

    if not data_inicio or not data_fim:
        return render_template('testeapi.html')
    else:
        if data_inicio and data_fim:
            try:
                data_inicio_formatted = datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%Y%m%d')
                data_fim_formatted = datetime.strptime(data_fim, '%Y-%m-%d').strftime('%Y%m%d')
            except ValueError:
                return "Formato de data inválido. Por favor, insira as datas no formato correto."

            url_api_crm = f"https://ap5tntnr6b.execute-api.us-east-1.amazonaws.com/api/transcrmc/{data_inicio_formatted}/{data_fim_formatted}"
            dados_api_crm = obter_dados_da_api(url_api_crm)

            search_query = request.args.get('search', '')

            if dados_api_crm:
                if search_query:
                    dados_api_crm = [item for item in dados_api_crm if search_query.lower() in item['Cliente'].lower()]
                    
                dados_formatados = [(item['Id_Cliente'], item['Cliente'], item['Pedidos'], item['Token']) for item in dados_api_crm]

                tokens = [item['Token'] for item in dados_api_crm]
                resultado_final = await consulta_api_box(tokens, data_inicio, data_fim)

                return render_template('testeapi.html', dados=dados_formatados, data_inicio=data_inicio, data_fim=data_fim, resultado_final=resultado_final)
            else:
                return "Erro ao obter dados da primeira API"


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
                error = "A resposta da API está vazia. Verifique os dados e tente novamente."
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

    # Adicionando o cabeçalho ao PDF
    frame = Frame(pdf.leftMargin, pdf.bottomMargin, pdf.width, pdf.height - 2 * 50, id='normal')
    template = PageTemplate(id='test', frames=[frame], onPage=lambda canvas, doc: header(canvas, doc, pini, pfin, cliente, estado))

    pdf.addPageTemplates([template])

    # Construindo o PDF
    pdf.build(elements)

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


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
