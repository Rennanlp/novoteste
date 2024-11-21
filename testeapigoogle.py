import gspread
from google.oauth2.service_account import Credentials
import traceback
def acessar_planilha_forms():
    # Defina o escopo de acesso
    escopo = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    # Caminho para o arquivo JSON da conta de serviço
    caminho_credenciais = "credentials.json"

    try:
        # Carrega as credenciais com google-auth
        credenciais = Credentials.from_service_account_file(caminho_credenciais, scopes=escopo)
        cliente = gspread.authorize(credenciais)

        # ID da planilha (copie do URL)
        planilha_id = "13Ivq0l0ueMB6GjO0xr6umLx7qHMvPJRAomjgxf3CunE"

        # Acessar a planilha pelo ID
        planilha = cliente.open_by_key(planilha_id)

        # Acessar a aba "Form Responses 1"
        aba_forms = planilha.worksheet("Respostas ao formulário 1")
        dados = aba_forms.get_all_records()

        print("Dados recebidos do Google Forms:")
        for linha in dados:
            print(linha)

    except gspread.exceptions.SpreadsheetNotFound:
        print("Erro: A planilha com o ID fornecido não foi encontrada.")
    except Exception as e:
        print("Um erro ocorreu.")
        print("Detalhes do erro:")
        traceback.print_exc()  # Mostra o erro completo

if __name__ == "__main__":
    acessar_planilha_forms()
