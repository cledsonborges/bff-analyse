from flask import Blueprint, request, jsonify
import logging
import os
from services.backlog_analysis import BacklogAnalysisService
from services.jira_integration import JiraIntegrationService
from services.google_play_scraping_real import GooglePlayScrapingService
from services.apple_store_scraping_real import AppleAppStoreScrapingService

logger = logging.getLogger(__name__)

# Criar blueprint
backlog_bp = Blueprint('backlog', __name__)

# Inicializar serviços
backlog_service = BacklogAnalysisService(api_key=os.getenv("GEMINI_API_KEY"))
google_play_service = GooglePlayScrapingService()
apple_store_service = AppleAppStoreScrapingService()

@backlog_bp.route("/backlog/analyze", methods=["POST"])
def analyze_app_backlog():
    """
    Analisa reviews de um app e gera backlog com IA
    ---
    tags:
      - Backlog
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            app_id:
              type: string
              description: ID do aplicativo
            store:
              type: string
              enum: [google_play, app_store]
              description: Loja do aplicativo
            app_name:
              type: string
              description: Nome do aplicativo
            limit:
              type: integer
              default: 100
              description: Número máximo de reviews para análise
          required:
            - app_id
            - store
            - app_name
    responses:
      200:
        description: Backlog gerado com sucesso
        schema:
          type: object
          properties:
            success:
              type: boolean
            backlog_data:
              type: object
            message:
              type: string
      400:
        description: Parâmetros inválidos
      500:
        description: Erro interno do servidor
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados JSON são obrigatórios"}), 400
        
        app_id = data.get('app_id')
        store = data.get('store')
        app_name = data.get('app_name')
        limit = data.get('limit', 100)
        
        if not all([app_id, store, app_name]):
            return jsonify({"error": "app_id, store e app_name são obrigatórios"}), 400
        
        if store not in ['google_play', 'app_store']:
            return jsonify({"error": "store deve ser 'google_play' ou 'app_store'"}), 400
        
        # Buscar reviews do app
        logger.info(f"Buscando reviews para {app_name} ({app_id}) na {store}")
        
        reviews_data = []
        if store == "google_play":
            reviews_data, _ = google_play_service.get_app_reviews(app_id, count=limit)
        elif store == "app_store":
            reviews_data = apple_store_service.get_app_reviews(app_id, limit=limit)
        
        if not reviews_data:
            return jsonify({
                "success": False,
                "message": "Nenhuma review encontrada para análise",
                "backlog_data": None
            }), 200
        
        # Analisar reviews e gerar backlog
        logger.info(f"Analisando {len(reviews_data)} reviews com IA")
        backlog_data = backlog_service.analyze_reviews_for_backlog(reviews_data, app_name)
        
        # Gerar recomendações de sprint
        sprint_recommendations = backlog_service.generate_sprint_recommendations(backlog_data)
        backlog_data['sprint_recommendations'] = sprint_recommendations
        
        return jsonify({
            "success": True,
            "message": f"Backlog gerado com sucesso para {app_name}",
            "backlog_data": backlog_data
        })
        
    except Exception as e:
        logger.error(f"Erro na análise de backlog: {e}")
        return jsonify({"error": f"Erro interno do servidor: {str(e)}"}), 500

@backlog_bp.route("/backlog/create-jira-issues", methods=["POST"])
def create_jira_issues():
    """
    Cria issues no Jira baseadas no backlog gerado
    ---
    tags:
      - Backlog
      - Jira
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            backlog_data:
              type: object
              description: Dados do backlog gerado pela IA
            project_key:
              type: string
              description: Chave do projeto Jira
            jira_config:
              type: object
              properties:
                jira_url:
                  type: string
                  description: URL do Jira
                email:
                  type: string
                  description: Email do usuário Jira
                api_token:
                  type: string
                  description: Token de API do Jira
              required:
                - jira_url
                - email
                - api_token
          required:
            - backlog_data
            - project_key
            - jira_config
    responses:
      200:
        description: Issues criadas com sucesso
      400:
        description: Parâmetros inválidos
      500:
        description: Erro interno do servidor
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados JSON são obrigatórios"}), 400
        
        backlog_data = data.get('backlog_data')
        project_key = data.get('project_key')
        jira_config = data.get('jira_config')
        
        if not all([backlog_data, project_key, jira_config]):
            return jsonify({"error": "backlog_data, project_key e jira_config são obrigatórios"}), 400
        
        # Validar configuração do Jira
        required_jira_fields = ['jira_url', 'email', 'api_token']
        for field in required_jira_fields:
            if field not in jira_config:
                return jsonify({"error": f"jira_config.{field} é obrigatório"}), 400
        
        # Inicializar serviço Jira
        jira_service = JiraIntegrationService(
            jira_url=jira_config['jira_url'],
            email=jira_config['email'],
            api_token=jira_config['api_token']
        )
        
        # Testar conexão
        connection_test = jira_service.test_connection()
        if not connection_test.get('success'):
            return jsonify({
                "error": "Falha na conexão com Jira",
                "details": connection_test.get('message')
            }), 400
        
        # Criar issues
        logger.info(f"Criando issues no projeto {project_key}")
        result = jira_service.create_backlog_issues(project_key, backlog_data)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro ao criar issues no Jira: {e}")
        return jsonify({"error": f"Erro interno do servidor: {str(e)}"}), 500

@backlog_bp.route("/jira/test-connection", methods=["POST"])
def test_jira_connection():
    """
    Testa conexão com Jira
    ---
    tags:
      - Jira
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            jira_url:
              type: string
              description: URL do Jira
            email:
              type: string
              description: Email do usuário Jira
            api_token:
              type: string
              description: Token de API do Jira
          required:
            - jira_url
            - email
            - api_token
    responses:
      200:
        description: Resultado do teste de conexão
      400:
        description: Parâmetros inválidos
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados JSON são obrigatórios"}), 400
        
        jira_url = data.get('jira_url')
        email = data.get('email')
        api_token = data.get('api_token')
        
        if not all([jira_url, email, api_token]):
            return jsonify({"error": "jira_url, email e api_token são obrigatórios"}), 400
        
        # Testar conexão
        jira_service = JiraIntegrationService(jira_url, email, api_token)
        result = jira_service.test_connection()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão Jira: {e}")
        return jsonify({"error": f"Erro interno do servidor: {str(e)}"}), 500

@backlog_bp.route("/jira/projects", methods=["POST"])
def get_jira_projects():
    """
    Obtém lista de projetos Jira
    ---
    tags:
      - Jira
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            jira_url:
              type: string
              description: URL do Jira
            email:
              type: string
              description: Email do usuário Jira
            api_token:
              type: string
              description: Token de API do Jira
          required:
            - jira_url
            - email
            - api_token
    responses:
      200:
        description: Lista de projetos
      400:
        description: Parâmetros inválidos
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados JSON são obrigatórios"}), 400
        
        jira_url = data.get('jira_url')
        email = data.get('email')
        api_token = data.get('api_token')
        
        if not all([jira_url, email, api_token]):
            return jsonify({"error": "jira_url, email e api_token são obrigatórios"}), 400
        
        # Buscar projetos
        jira_service = JiraIntegrationService(jira_url, email, api_token)
        projects = jira_service.get_projects()
        
        return jsonify({
            "success": True,
            "projects": projects
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar projetos Jira: {e}")
        return jsonify({"error": f"Erro interno do servidor: {str(e)}"}), 500

