from flask import Flask
from flasgger import Swagger

def init_swagger(app: Flask):
    """Inicializa o Swagger para a aplicação Flask"""
    
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/swagger/"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "BFF Analyse API",
            "description": "API para análise de aplicativos móveis e reviews",
            "version": "3.0.0",
            "contact": {
                "name": "Cledson Alves",
                "email": "cledsonborges@gmail.com"
            }
        },
        "host": "localhost:5002",
        "basePath": "/",
        "schemes": ["http", "https"],
        "consumes": ["application/json"],
        "produces": ["application/json"],
        "tags": [
            {
                "name": "Apps",
                "description": "Operações relacionadas aos aplicativos"
            },
            {
                "name": "Reviews",
                "description": "Operações relacionadas às reviews"
            },
            {
                "name": "Analysis",
                "description": "Operações de análise de sentimentos"
            },
            {
                "name": "Scraping",
                "description": "Operações de coleta de dados"
            },
            {
                "name": "Health",
                "description": "Verificação de saúde da API"
            }
        ],
        "definitions": {
            "App": {
                "type": "object",
                "properties": {
                    "app_id": {"type": "string", "description": "ID único do aplicativo"},
                    "name": {"type": "string", "description": "Nome do aplicativo"},
                    "store": {"type": "string", "enum": ["google_play", "app_store"], "description": "Loja do aplicativo"},
                    "current_version": {"type": "string", "description": "Versão atual"},
                    "rating": {"type": "number", "format": "float", "description": "Avaliação média"},
                    "total_reviews": {"type": "integer", "description": "Total de reviews"},
                    "category": {"type": "string", "description": "Categoria do app"},
                    "description": {"type": "string", "description": "Descrição do app"},
                    "icon_url": {"type": "string", "description": "URL do ícone"},
                    "last_updated": {"type": "string", "format": "date-time", "description": "Última atualização"}
                }
            },
            "Review": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "ID da review"},
                    "user_name": {"type": "string", "description": "Nome do usuário"},
                    "content": {"type": "string", "description": "Conteúdo da review"},
                    "rating": {"type": "integer", "minimum": 1, "maximum": 5, "description": "Avaliação (1-5)"},
                    "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"], "description": "Sentimento"},
                    "sentiment_score": {"type": "number", "format": "float", "description": "Score do sentimento"},
                    "date": {"type": "string", "format": "date-time", "description": "Data da review"}
                }
            },
            "Analysis": {
                "type": "object",
                "properties": {
                    "total_reviews": {"type": "integer", "description": "Total de reviews analisadas"},
                    "positive_percentage": {"type": "number", "format": "float", "description": "Percentual positivo"},
                    "negative_percentage": {"type": "number", "format": "float", "description": "Percentual negativo"},
                    "neutral_percentage": {"type": "number", "format": "float", "description": "Percentual neutro"},
                    "avg_sentiment_score": {"type": "number", "format": "float", "description": "Score médio de sentimento"},
                    "last_updated": {"type": "string", "format": "date-time", "description": "Última atualização"}
                }
            },
            "HealthCheck": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Status da API"},
                    "message": {"type": "string", "description": "Mensagem de status"},
                    "version": {"type": "string", "description": "Versão da API"},
                    "database": {"type": "string", "description": "Status do banco"},
                    "stats": {
                        "type": "object",
                        "properties": {
                            "total_apps": {"type": "integer"},
                            "total_reviews": {"type": "integer"}
                        }
                    }
                }
            },
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "string", "description": "Mensagem de erro"}
                }
            }
        }
    }
    
    return Swagger(app, config=swagger_config, template=swagger_template)

