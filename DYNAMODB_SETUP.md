# Configuração do DynamoDB para Registro de Usuários

## Visão Geral

Este sistema foi configurado para registrar automaticamente usuários no DynamoDB da AWS quando fazem login na aplicação. 

## Funcionalidades Implementadas

### 1. Registro Automático de Usuários
- Quando um usuário faz login via `/api/auth/login`, seus dados são automaticamente registrados na tabela `Users` do DynamoDB
- Dados registrados incluem:
  - Email do usuário
  - Timestamp de criação
  - Timestamp do último login
  - Contador de logins
  - User Agent do navegador
  - Endereço IP

### 2. Novas Rotas da API

#### GET `/api/users/stats/<email>`
Obtém estatísticas de um usuário específico.
- Requer autenticação JWT
- Retorna: email, login_count, created_at, last_login, updated_at

#### GET `/api/users/recent?limit=10`
Lista usuários mais recentes.
- Requer autenticação JWT
- Parâmetro opcional: `limit` (padrão: 10)
- Retorna lista de usuários ordenados por último login

## Configuração

### 1. Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e configure as seguintes variáveis:

```bash
# Credenciais AWS
AWS_ACCESS_KEY_ID=sua_access_key_aqui
AWS_SECRET_ACCESS_KEY=sua_secret_key_aqui
AWS_REGION=us-east-2

# Outras configurações
JWT_SECRET_KEY=sua_chave_jwt_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui
```

### 2. Tabela DynamoDB

A aplicação espera uma tabela chamada `Users` no DynamoDB com:
- **Partition Key**: `email` (String)
- **Região**: us-east-2 (configurável via AWS_REGION)

### 3. Permissões IAM

O usuário AWS precisa das seguintes permissões na tabela `Users`:
- `dynamodb:GetItem`
- `dynamodb:PutItem`
- `dynamodb:Scan`
- `dynamodb:Query`

## Instalação de Dependências

```bash
pip install -r requirements.txt
```

## Teste do Sistema

Execute o script de teste para verificar se tudo está funcionando:

```bash
# Configure as variáveis de ambiente primeiro
export AWS_ACCESS_KEY_ID=sua_access_key
export AWS_SECRET_ACCESS_KEY=sua_secret_key
export AWS_REGION=us-east-2

# Execute o teste
python3 test_user_system.py
```

## Estrutura de Dados no DynamoDB

Exemplo de registro na tabela `Users`:

```json
{
  "email": "usuario@exemplo.com",
  "created_at": "2025-06-25T10:00:00.000000+00:00",
  "last_login": "2025-06-25T10:00:00.000000+00:00",
  "updated_at": "2025-06-25T10:00:00.000000+00:00",
  "login_count": 1,
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.1"
}
```

## Arquivos Modificados

- `api.py` - Integração do UserService na rota de login e novas rotas
- `services/user_service.py` - Serviço para gerenciar usuários no DynamoDB
- `requirements.txt` - Adicionada dependência boto3
- `test_user_system.py` - Script de teste do sistema

## Tratamento de Erros

O sistema foi projetado para ser resiliente:
- Se o DynamoDB não estiver disponível, o login ainda funciona (apenas não registra)
- Logs detalhados para debugging
- Tratamento adequado de tipos Decimal do DynamoDB
- Validação de dados de entrada

## Monitoramento

Os logs da aplicação incluem:
- Sucessos e falhas de registro no DynamoDB
- Estatísticas de acesso dos usuários
- Erros de conectividade com AWS

Para monitorar em produção, verifique os logs da aplicação e as métricas do DynamoDB no AWS CloudWatch.

