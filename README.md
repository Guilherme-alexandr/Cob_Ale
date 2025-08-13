# 💰 CobAle - Sistema de Cobrança

CobAle é um sistema de cobrança desenvolvido em Flask como projeto pessoal durante as férias. O objetivo é simular a estrutura de uma API completa com microsserviço, regras de negócio, organização em camadas e controle de acordos de pagamento sobre contratos em atraso.

---

## 🧩 Tecnologias Utilizadas

- Python 3.11+
- Flask
- Flask SQLAlchemy
- Flask Migrate
- SQLite (padrão, pode ser adaptado para outros bancos)
- Swagger (documentação finalizada)

---

## 📦 Entidades do Sistema

### 👤 Cliente
Armazena os dados dos clientes devedores.

| Campo    | Tipo     | Obrigatório | Observações                    |
|----------|----------|-------------|--------------------------------|
| id       | Integer  | Sim         | Gerado automaticamente         |
| nome     | String   | Sim         |                                |
| cpf      | String   | Sim         | Único, 11 dígitos              |
| numero   | String   | Sim         | Telefone com DDD               |
| email    | String   | Sim         | Único                          |

---

### 📄 Contrato
Representa um débito associado a um cliente, podendo ser negociado.

| Campo                    | Tipo     | Obrigatório | Observações                         |
|--------------------------|----------|-------------|-------------------------------------|
| numero_contrato          | String   | Sim         | 6 dígitos, gerado automaticamente   |
| cliente_id               | Integer  | Sim         | Relacionado ao cliente              |
| data_emissao             | DateTime | Automático  |                                     |
| data_vencimento_original | DateTime | Sim         | Define início do atraso             |
| valor_total              | Float    | Sim         | Valor original do débito            |
| filial                   | String   | Sim         | Nome da loja                        |

---

### 🤝 Acordo
Define a negociação feita sobre um contrato. Pode ser à vista ou parcelado (até 24x).

| Campo          | Tipo     | Observações                                 |
|----------------|----------|---------------------------------------------|
| id             | Integer  | Gerado automaticamente                      |
| contrato_id    | String   | Referência ao contrato                      |
| tipo_pagamento | String   | "avista" ou "parcelado"                     |
| qtd_parcelas   | Integer  | Obrigatório se for parcelado                |
| valor_total    | Float    | Já com juros e descontos aplicados          |
| vencimento     | Date     | Data de vencimento do acordo ou 1ª parcela  |
| status         | String   | em andamento, finalizado, quebrado          |

---

## ⚙️ Como rodar localmente

1. **Clone o projeto**
   ```bash
   git clone https://github.com/Guilherme-alexandr/Cob_Ale.git
   cd Cob_Ale
   ```

2. **Crie e ative um ambiente virtual (opcional, mas recomendado)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Inicie o banco de dados**
   ```bash
   flask shell
   >>> from app.database import db
   >>> db.create_all()
   >>> exit()
   ```

5. **Rode a API principal**
   ```bash
   flask run
   ```

---

## 📥 Exemplos de Entrada (JSON)

### 👨🏿 Criar Cliente
```json
{
  "nome": "João da Silva",
  "cpf": "12345678901",
  "numero": "11999998888",
  "email": "joao.silva@email.com"
}
```

### 🧾 Criar Contrato
```json
{
  "cliente_id": 1,
  "valor_total": 450.75,
  "filial": "Loja Central",
  "data_vencimento_original": "2025-05-30"
}
```

### 📑 Criar Acordo
```json
{
  "contrato_id": "000001",
  "tipo_pagamento": "parcelado",
  "qtd_parcelas": 4,
  "vencimento": "2025-08-10"
}
```

### 📊 Simular Acordo
```json
{
  "valor_original": 2194.32,
  "dias_em_atraso": 135,
  "tipo_pagamento": "parcelado",
  "quantidade_parcelas": 2,
  "valor_entrada": 0
}
```