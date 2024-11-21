from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_paginate import Pagination

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo Reverso
class Reverso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    remetente = db.Column(db.String(100), nullable=False)
    cliente = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    imagem = db.Column(db.String(255))

# Rota para listar reversos com busca e paginação
@app.route('/reversos', methods=['GET'])
def reversos():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    if query:
        reversos = Reverso.query.filter(Reverso.cliente.contains(query) | Reverso.remetente.contains(query)).paginate(page, 10, False)
    else:
        reversos = Reverso.query.paginate(page, 10, False)

    return render_template('listar_reversos.html', reversos=reversos, query=query)

# Rota para adicionar um reverso
@app.route('/reversos/adicionar', methods=['GET', 'POST'])
def adicionar_reverso():
    if request.method == 'POST':
        remetente = request.form['remetente']
        cliente = request.form['cliente']
        descricao = request.form['descricao']
        imagem = request.files['imagem'] if 'imagem' in request.files else None

        # Salve a imagem e o reverso no banco de dados (salvamento da imagem não mostrado)

        novo_reverso = Reverso(remetente=remetente, cliente=cliente, descricao=descricao, imagem=imagem.filename if imagem else None)
        db.session.add(novo_reverso)
        db.session.commit()

        return redirect(url_for('reversos'))

    return render_template('adicionar_reverso.html')

if __name__ == "__main__":
    app.run(debug=True)
