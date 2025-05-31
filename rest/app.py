import os
from flask import Flask, request, jsonify
import pyodbc
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
import base64

app = Flask(__name__)

# Configurações do Banco de Dados SQL Server
# Substitua pelos valores do seu Azure SQL Server
DB_SERVER = os.environ.get("DB_SERVER", "quitandaonlinesqlserver.database.windows.net")
DB_DATABASE = os.environ.get("DB_DATABASE", "QuitandaProdutosDB")
DB_USERNAME = os.environ.get("DB_USERNAME", "quitandaadmin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "SuaSenhaSegura!123") # Use a senha que você definiu

# Configurações do Azure Blob Storage
# Substitua pelos valores da sua Conta de Armazenamento
STORAGE_ACCOUNT_NAME = os.environ.get("STORAGE_ACCOUNT_NAME", "quitandaonlineimages")
STORAGE_ACCOUNT_KEY = os.environ.get("STORAGE_ACCOUNT_KEY", "SUA_CHAVE_DE_ARMAZENAMENTO_AQUI") # A chave que o CLI retornou
CONTAINER_NAME = "product-images"

# Conexão com o Banco de Dados
def get_db_connection():
    cnxn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_DATABASE};"
        f"UID={DB_USERNAME};"
        f"PWD={DB_PASSWORD}"
    )
    return cnxn

# Configurações do Blob Service Client
blob_service_client = BlobServiceClient(account_url=f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
                                        credential=STORAGE_ACCOUNT_KEY)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)


# Endpoint para obter todos os produtos (READ)
@app.route('/produtos', methods=['GET'])
def get_produtos():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ProdutoID, Nome, Tipo, Preco, Origem, Fornecedor, Estoque, ImagemUrl FROM Produtos")
        produtos = []
        for row in cursor.fetchall():
            produtos.append({
                "ProdutoID": row[0],
                "Nome": row[1],
                "Tipo": row[2],
                "Preco": float(row[3]),
                "Origem": row[4],
                "Fornecedor": row[5],
                "Estoque": row[6],
                "ImagemUrl": row[7]
            })
        return jsonify(produtos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint para obter um produto por ID (READ)
@app.route('/produtos/<int:produto_id>', methods=['GET'])
def get_produto_by_id(produto_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ProdutoID, Nome, Tipo, Preco, Origem, Fornecedor, Estoque, ImagemUrl FROM Produtos WHERE ProdutoID=?", produto_id)
        row = cursor.fetchone()
        if row:
            produto = {
                "ProdutoID": row[0],
                "Nome": row[1],
                "Tipo": row[2],
                "Preco": float(row[3]),
                "Origem": row[4],
                "Fornecedor": row[5],
                "Estoque": row[6],
                "ImagemUrl": row[7]
            }
            return jsonify(produto)
        else:
            return jsonify({"message": "Produto não encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint para criar um novo produto (CREATE)
@app.route('/produtos', methods=['POST'])
def create_produto():
    data = request.json
    nome = data.get('Nome')
    tipo = data.get('Tipo')
    preco = data.get('Preco')
    origem = data.get('Origem')
    fornecedor = data.get('Fornecedor')
    estoque = data.get('Estoque')
    imagem_base64 = data.get('ImagemBase64') # Base64 da imagem

    if not nome:
        return jsonify({"message": "Nome do produto é obrigatório"}), 400

    image_url = None
    if imagem_base64:
        try:
            image_data = base64.b64decode(imagem_base64)
            # Gerar um nome de blob único
            blob_name = f"{nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png" # Ou .jpg dependendo do tipo

            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(image_data, overwrite=True)
            image_url = blob_client.url
        except Exception as e:
            return jsonify({"error": f"Erro ao fazer upload da imagem: {str(e)}"}), 500

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Produtos (Nome, Tipo, Preco, Origem, Fornecedor, Estoque, ImagemUrl) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nome, tipo, preco, origem, fornecedor, estoque, image_url)
        )
        conn.commit()
        return jsonify({"message": "Produto criado com sucesso", "ProdutoID": cursor.rowcount, "ImagemUrl": image_url}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint para atualizar um produto existente (UPDATE)
@app.route('/produtos/<int:produto_id>', methods=['PUT'])
def update_produto(produto_id):
    data = request.json
    nome = data.get('Nome')
    tipo = data.get('Tipo')
    preco = data.get('Preco')
    origem = data.get('Origem')
    fornecedor = data.get('Fornecedor')
    estoque = data.get('Estoque')
    imagem_base64 = data.get('ImagemBase64')

    image_url = None
    if imagem_base64:
        try:
            image_data = base64.b64decode(imagem_base64)
            # Para atualização, você pode gerar um novo blob ou atualizar o existente
            # Para simplificar aqui, vamos criar um novo blob com um nome diferente
            blob_name = f"{nome.replace(' ', '_')}_updated_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(image_data, overwrite=True)
            image_url = blob_client.url
        except Exception as e:
            return jsonify({"error": f"Erro ao fazer upload da imagem: {str(e)}"}), 500

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Construir a query de atualização dinamicamente
        updates = []
        params = []
        if nome is not None:
            updates.append("Nome=?")
            params.append(nome)
        if tipo is not None:
            updates.append("Tipo=?")
            params.append(tipo)
        if preco is not None:
            updates.append("Preco=?")
            params.append(preco)
        if origem is not None:
            updates.append("Origem=?")
            params.append(origem)
        if fornecedor is not None:
            updates.append("Fornecedor=?")
            params.append(fornecedor)
        if estoque is not None:
            updates.append("Estoque=?")
            params.append(estoque)
        if image_url is not None:
            updates.append("ImagemUrl=?")
            params.append(image_url)

        if not updates:
            return jsonify({"message": "Nenhum dado para atualizar fornecido"}), 400

        query = f"UPDATE Produtos SET {', '.join(updates)} WHERE ProdutoID=?"
        params.append(produto_id)

        cursor.execute(query, tuple(params))
        conn.commit()

        if cursor.rowcount > 0:
            return jsonify({"message": "Produto atualizado com sucesso", "ImagemUrl": image_url}), 200
        else:
            return jsonify({"message": "Produto não encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint para deletar um produto (DELETE)
@app.route('/produtos/<int:produto_id>', methods=['DELETE'])
def delete_produto(produto_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Opcional: Recuperar a ImagemUrl antes de deletar para remover o blob também
        cursor.execute("SELECT ImagemUrl FROM Produtos WHERE ProdutoID=?", produto_id)
        image_url_to_delete = cursor.fetchone()
        if image_url_to_delete and image_url_to_delete[0]:
            try:
                # Extrai o nome do blob da URL
                blob_name = image_url_to_delete[0].split('/')[-1].split('?')[0] # Remove query parameters if any
                blob_client = container_client.get_blob_client(blob_name)
                blob_client.delete_blob()
                print(f"Blob {blob_name} deletado com sucesso.")
            except Exception as e:
                print(f"Aviso: Não foi possível deletar o blob {image_url_to_delete[0]}: {str(e)}")


        cursor.execute("DELETE FROM Produtos WHERE ProdutoID=?", produto_id)
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({"message": "Produto deletado com sucesso"}), 200
        else:
            return jsonify({"message": "Produto não encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    # Para execução local:
    # app.run(debug=True)
    # Para permitir acesso externo (e.g., de Docker ou VMs):
    app.run(debug=True, host='0.0.0.0', port=5000)
