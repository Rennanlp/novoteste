import http.client
import json

conn = http.client.HTTPSConnection("api.boxlink.com.br")
payload = ''
headers = {
   'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJqb25hc2dhcmNpYTY2NkBnbWFpbC5jb20iLCJVU0VSX0RFVEFJTFMiOnsidXNlcklkIjoxNTgzLCJtYXRyaXpJZCI6MTcsImZyYW5xdWlhSWQiOjksImNsaWVudGVJZCI6bnVsbH0sImV4cCI6NDQ4MDk3NDAwMH0.0ew6BIm8cr5neOgkO1371-BSDnWcdkMjsvHRzU9wcS8',
    'Content-Type': 'application/json'
}
conn.request("GET", "/v2/sellers", payload, headers)
res = conn.getresponse()
data = res.read()

# Decodificar o JSON retornado
decoded_data = json.loads(data)

# Iterar sobre os itens e exibir apenas id e nome fantasia
for seller in decoded_data:
    print("Id:", seller['id'])
    print("Nome Fantasia:", seller['nomeFantasia'])
    print()
