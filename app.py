# app.py
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from unidecode import unidecode
import os
import csv
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
