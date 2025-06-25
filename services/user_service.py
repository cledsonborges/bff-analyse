import boto3
import os
import logging
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError
from decimal import Decimal
import json

class DecimalEncoder(json.JSONEncoder):
    """Encoder personalizado para lidar com tipos Decimal do DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

def convert_decimals(obj):
    """Converte objetos Decimal em int ou float recursivamente"""
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj

class UserService:
    """Serviço para gerenciar usuários no DynamoDB"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Configurar credenciais AWS
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-2')
        
        # Inicializar cliente DynamoDB
        try:
            self.dynamodb = boto3.resource(
                'dynamodb',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            self.table = self.dynamodb.Table('Users')
            self.logger.info("Conexão com DynamoDB estabelecida com sucesso")
        except NoCredentialsError:
            self.logger.error("Credenciais AWS não encontradas")
            raise
        except Exception as e:
            self.logger.error(f"Erro ao conectar com DynamoDB: {e}")
            raise
    
    def register_user_login(self, email, additional_data=None):
        """
        Registra ou atualiza o login do usuário na tabela Users
        
        Args:
            email (str): Email do usuário
            additional_data (dict): Dados adicionais do usuário (opcional)
            
        Returns:
            dict: Resultado da operação
        """
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Dados básicos do usuário
            user_data = {
                'email': email,
                'last_login': timestamp,
                'updated_at': timestamp
            }
            
            # Adicionar dados extras se fornecidos
            if additional_data:
                user_data.update(additional_data)
            
            # Verificar se o usuário já existe
            existing_user = self.get_user_by_email(email)
            
            if existing_user:
                # Atualizar usuário existente
                user_data['login_count'] = existing_user.get('login_count', 0) + 1
                self.logger.info(f"Atualizando usuário existente: {email}")
            else:
                # Novo usuário
                user_data['created_at'] = timestamp
                user_data['login_count'] = 1
                self.logger.info(f"Registrando novo usuário: {email}")
            
            # Salvar no DynamoDB
            response = self.table.put_item(Item=user_data)
            
            self.logger.info(f"Usuário {email} registrado/atualizado com sucesso no DynamoDB")
            
            return {
                'success': True,
                'message': 'Usuário registrado/atualizado com sucesso',
                'user_data': user_data
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"Erro do DynamoDB ({error_code}): {error_message}")
            
            return {
                'success': False,
                'error': f"Erro do DynamoDB: {error_message}"
            }
            
        except Exception as e:
            self.logger.error(f"Erro inesperado ao registrar usuário {email}: {e}")
            
            return {
                'success': False,
                'error': f"Erro interno: {str(e)}"
            }
    
    def get_user_by_email(self, email):
        """
        Busca um usuário pelo email
        
        Args:
            email (str): Email do usuário
            
        Returns:
            dict: Dados do usuário ou None se não encontrado
        """
        try:
            response = self.table.get_item(Key={'email': email})
            user_data = response.get('Item')
            return convert_decimals(user_data) if user_data else None
            
        except ClientError as e:
            self.logger.error(f"Erro ao buscar usuário {email}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erro inesperado ao buscar usuário {email}: {e}")
            return None
    
    def get_user_stats(self, email):
        """
        Obtém estatísticas do usuário
        
        Args:
            email (str): Email do usuário
            
        Returns:
            dict: Estatísticas do usuário
        """
        try:
            user = self.get_user_by_email(email)
            
            if not user:
                return {
                    'success': False,
                    'error': 'Usuário não encontrado'
                }
            
            return {
                'success': True,
                'stats': convert_decimals({
                    'email': user['email'],
                    'login_count': user.get('login_count', 0),
                    'created_at': user.get('created_at'),
                    'last_login': user.get('last_login'),
                    'updated_at': user.get('updated_at')
                })
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas do usuário {email}: {e}")
            return {
                'success': False,
                'error': f"Erro interno: {str(e)}"
            }
    
    def list_recent_users(self, limit=10):
        """
        Lista usuários mais recentes
        
        Args:
            limit (int): Número máximo de usuários a retornar
            
        Returns:
            dict: Lista de usuários recentes
        """
        try:
            response = self.table.scan(
                Limit=limit,
                ProjectionExpression='email, created_at, last_login, login_count'
            )
            
            users = response.get('Items', [])
            
            # Ordenar por último login (mais recente primeiro)
            users.sort(key=lambda x: x.get('last_login', ''), reverse=True)
            
            return {
                'success': True,
                'users': convert_decimals(users[:limit]),
                'count': len(users)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao listar usuários recentes: {e}")
            return {
                'success': False,
                'error': f"Erro interno: {str(e)}"
            }

