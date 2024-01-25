# app.py
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from unidecode import unidecode
import pandas as pd
import os
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

            # Processar o conteúdo do arquivo CSV
            df = pd.read_csv(filepath, encoding='utf-8')
            df = df.applymap(lambda x: unidecode(str(x)) if pd.notna(x) else x)

            # Criar um buffer de bytes em memória para o novo CSV
            output_buffer = BytesIO()
            df.to_csv(output_buffer, index=False, encoding='utf-8')
            output_buffer.seek(0)

            current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_with_datetime = f'Arquivo_Ajustado_{current_datetime}.csv'
            return send_file(output_buffer, download_name=filename_with_datetime, as_attachment=True)

        except Exception as e:
            return "Erro durante o processamento do arquivo: {}".format(str(e))

    return "Tipo de arquivo não permitido."

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
