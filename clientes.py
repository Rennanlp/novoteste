import sqlite3
import pandas as pd

def criar_banco_dados():
    conn = sqlite3.connect('responsaveis.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dados (
            id INTEGER PRIMARY KEY,
            responsavel TEXT,
            empresa TEXT,
            cd INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

def inserir_dados(responsavel, empresa, cd):
    conn = sqlite3.connect('responsaveis.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO dados (responsavel, empresa, cd)
        VALUES (?, ?, ?)
    ''', (responsavel, empresa, cd))
    
    conn.commit()
    conn.close()

def inserir_dados_da_planilha(df):
    for index, row in df.iterrows():
        inserir_dados(row['Responsavel'], row['Empresa'], row['CD'])
        
def obter_responsaveis_e_empresas():
    conn = sqlite3.connect('responsaveis.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT responsavel, empresa FROM dados")
    responsaveis_empresas = cursor.fetchall()
    
    conn.close()
    
    return responsaveis_empresas
