import json
import requests

codigo = 'QQ308210136BR'
url = f'https://i6r0uqmq25.execute-api.us-east-1.amazonaws.com/api/track/{codigo}'


response = requests.get(url)

if response.status_code == 200:

    resultado = response.json()
    
    
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
else:
    print(f'Erro na requisição. Código de status: {response.status_code}')
