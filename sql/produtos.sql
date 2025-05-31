CREATE TABLE Produtos (
    ProdutoID INT IDENTITY(1,1) PRIMARY KEY,
    Nome NVARCHAR(255) NOT NULL,
    Tipo NVARCHAR(255),
    Preco DECIMAL(10, 2),
    Origem NVARCHAR(255),
    Fornecedor NVARCHAR(255),
    Estoque INT,
    ImagemUrl NVARCHAR(MAX)
);
