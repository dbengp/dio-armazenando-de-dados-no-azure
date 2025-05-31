# dio-armazenando-de-dados-no-azure
## projeto de demonstração do Armazenando dados de um E-Commerce na Cloud

### Os conceitos e resumo foram retirados da leitura da documentação oficial: <https://learn.microsoft.com/pt-br/azure/storage/common/storage-account-overview> e <https://learn.microsoft.com/pt-br/sql/sql-server/what-is-sql-server?view=sql-server-ver17>

### O Azure oferece uma "caixa de ferramentas" diversificada de serviços de armazenamento, permitindo que você escolha a solução mais adequada para cada tipo de dado e requisito da sua aplicação. Nesse projeto, foca-se em dois tipos de armazenamento no Azure: Contas de Armazenamento e Azure SQL Server/Database. Juntos, eles oferecem uma solução robusta para o cenário da quitanda online, mas o Azure possui um ecossistema muito mais amplo de serviços de dados.

### Azure Storage Accounts (Armazenamento de Objetos - Blobs)
- Blobs: Perfeitos para armazenar arquivos como imagens, vídeos, documentos, backups e logs. Eles são acessados via URL e oferecem escalabilidade massiva e baixo custo. Você pode escolher diferentes camadas de acesso (hot, cool, cold, archive) para otimizar custos com base na frequência de acesso.
- Além dos blobs, as Contas de Armazenamento também podem hospedar:
  * Filas (Queues): Para mensagens de longa duração entre componentes de aplicativos, útil para desacoplar microsserviços.
  * Tabelas (Tables): Um armazenamento NoSQL de chave-valor para dados semi-estruturados, oferecendo alta disponibilidade e escalabilidade.
  * Compartilhamentos de Arquivos (File Shares): Para compartilhamentos de arquivos de rede totalmente gerenciados, acessíveis via SMB, ideais para migrar aplicações on-premises para a nuvem.

### Azure SQL Database (Banco de Dados Relacional)
- Azure SQL Database: É a escolha ideal para dados estruturados e relacionais, este é um serviço de banco de dados relacional (PaaS - Platform as a Service) altamente escalável e gerenciado, baseado no Microsoft SQL Server. Ele oferece consistência ACID, suporte a transações complexas, alta disponibilidade embutida, recuperação de desastres e segurança robusta. Permite consultas SQL familiares e integra-se bem com outras ferramentas Microsoft.

### Outras Opções de Armazenamento no Azure
- o Azure oferece uma vasta gama de outros serviços de dados, cada um otimizado para diferentes cenários:
  * Azure Cosmos DB: Um banco de dados NoSQL multimodelo e distribuído globalmente, ideal para aplicações com requisitos de baixa latência e alta escalabilidade em nível global.
  * Azure Database for PostgreSQL/MySQL/MariaDB: Serviços de banco de dados relacional gerenciados para engines open-source populares.
  * Azure Synapse Analytics: Um serviço de análise ilimitado que reúne data warehousing corporativo e análise de big data.
  * Azure Data Lake Storage: Um repositório altamente escalável para dados de big data, construído sobre o Azure Blob Storage.
  * Azure Cache for Redis: Um cache de dados na memória para aplicações que precisam de acesso rápido a dados.

### Cenário de e-commmerce
- A titulo de demonstração é apresentado um Cenário de e-commmerce no qual existe uma quintanda online que vende uma quantidade muito diversificada de frutas, verduras, legumes, ervas e especiarias disponibilizados como produtos dessa quintanda que devem ser armazenados em um banco de dados do SQL Server com seguintes características: nome, tipo, preço, origem, fornecedor, estoque, imagem. Este último atributo ficará armazenado em alguns blobs de uma conta de armazenamento do Azure. Por fim, foi criada uma Aplicação REST simples em Pyhton que disponibilize endpoints de CRUD às operações desse e-commerce.
- Recursos do Azure: como demonstração, uso o Azure CLI para criar o Servidor SQL do Azure, o Banco de Dados SQL do Azure e a Conta de Armazenamento do Azure.
```
# 1. Configurar variáveis (substitua pelos seus valores)
RESOURCE_GROUP_NAME="QuitandaOnlineRG"
LOCATION="eastus" # Escolha a região mais próxima de você
SQL_SERVER_NAME="quitandaonlinesqlserver"
SQL_ADMIN_USER="quitandaadmin"
SQL_ADMIN_PASSWORD="SuaSenhaSegura!123" # Altere para uma senha forte
SQL_DATABASE_NAME="QuitandaProdutosDB"
STORAGE_ACCOUNT_NAME="quitandaonlineimages" # Nome da conta de armazenamento deve ser globalmente único

# 2. Criar Grupo de Recursos
az group create --name $RESOURCE_GROUP_NAME --location $LOCATION

# 3. Criar Servidor SQL do Azure
az sql server create \
    --name $SQL_SERVER_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --location $LOCATION \
    --admin-user $SQL_ADMIN_USER \
    --admin-password $SQL_ADMIN_PASSWORD

# 4. Configurar regra de firewall para permitir acesso de sua máquina (ou de onde a aplicação rodará)
# Obtenha seu IP público: você pode visitar "whatismyip.com" ou usar um comando como:
# curl -s checkip.amazonaws.com
YOUR_PUBLIC_IP="0.0.0.0" # Substitua pelo seu IP público ou 0.0.0.0 para acesso de qualquer IP (NÃO RECOMENDADO EM PRODUÇÃO)
az sql server firewall-rule create \
    --resource-group $RESOURCE_GROUP_NAME \
    --server $SQL_SERVER_NAME \
    --name AllowMyIP \
    --start-ip-address $YOUR_PUBLIC_IP \
    --end-ip-address $YOUR_PUBLIC_IP

# Ou para permitir acesso de serviços Azure (se sua aplicação estiver hospedada no Azure)
# az sql server firewall-rule create \
#    --resource-group $RESOURCE_GROUP_NAME \
#    --server $SQL_SERVER_NAME \
#    --name AllowAzureServices \
#    --start-ip-address 0.0.0.0 \
#    --end-ip-address 0.0.0.0

# 5. Criar Banco de Dados SQL do Azure
az sql db create \
    --resource-group $RESOURCE_GROUP_NAME \
    --server $SQL_SERVER_NAME \
    --name $SQL_DATABASE_NAME \
    --edition Basic \
    --service-objective Basic

# 6. Criar Conta de Armazenamento do Azure
az storage account create \
    --name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --location $LOCATION \
    --sku Standard_LRS \
    --kind StorageV2

# 7. Criar um contêiner de blob para as imagens dos produtos
STORAGE_KEY=$(az storage account keys list \
                --resource-group $RESOURCE_GROUP_NAME \
                --account-name $STORAGE_ACCOUNT_NAME \
                --query "[0].value" -o tsv)

az storage container create \
    --name "product-images" \
    --account-name $STORAGE_ACCOUNT_NAME \
    --account-key $STORAGE_KEY \
    --public-access blob # Ou off para acesso privado e gerar SAS tokens

echo "Recursos Azure criados com sucesso!"
echo "Servidor SQL: $SQL_SERVER_NAME.database.windows.net"
echo "Banco de Dados SQL: $SQL_DATABASE_NAME"
echo "Conta de Armazenamento: $STORAGE_ACCOUNT_NAME"
echo "Chave de Armazenamento (para uso em sua aplicação): $STORAGE_KEY"
```
- Observações (reforçando que se trata de uma demonstração!):
- SKU do SQL DB: Basic é para testes/desenvolvimento. Para produção, escolha um SKU e Service Objective adequados às suas necessidades de desempenho (e.g., Standard ou Premium).
- SKU da Conta de Armazenamento: Standard_LRS é para redundância local. Considere Standard_GRS ou Standard_RAGRS para maior durabilidade em produção.
- Segurança: A regra de firewall AllowMyIP é para desenvolvimento. Em produção, configure regras de firewall mais restritivas ou use VNet Service Endpoints/Private Link. Evite 0.0.0.0 em produção.
- Acesso Público do Blob: public-access blob permite que blobs sejam acessados diretamente pela URL. Se precisar de mais controle, use off e gere Shared Access Signatures (SAS) para acesso temporário e controlado.

### Aplicação REST Simples em Python com Flask
- A aplicação Python usará o Flask para criar a API REST, pyodbc para conectar ao SQL Server e azure-storage-blob para interagir com o Azure Storage. Pré-requisitos: Python 3.x instalado, instale os pacotes necessários: `pip install Flask pyodbc azure-storage-blob`

















