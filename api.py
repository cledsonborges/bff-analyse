from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
import re
import jwt
from datetime import datetime, timezone, timedelta
from flasgger import swag_from
from swagger_config import init_swagger

# Importar serviços de scraping e análise de sentimentos
from services.google_play_scraping_real import GooglePlayScrapingService
from services.apple_store_scraping_real import AppleAppStoreScrapingService
from services.sentiment_analysis_real import SentimentAnalysisService

# Configurar API Key do Gemini
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "AIzaSyA_dmMQb9pOglYE-O5325CdIqmoCloVSLI")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Configurar chave secreta para JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'itau-bff-secret-key-2024')

# Inicializar Swagger
swagger = init_swagger(app)

# Inicializar serviços
google_play_service = GooglePlayScrapingService()
apple_store_service = AppleAppStoreScrapingService()
sentiment_service = SentimentAnalysisService(api_key=os.getenv("GEMINI_API_KEY"))

# Importar e registrar blueprints
try:
    from routes.scraping_real import scraping_bp
    app.register_blueprint(scraping_bp, url_prefix="/api")
    logger.info("Blueprint de scraping registrado")
except ImportError as e:
    logger.warning(f"Não foi possível importar blueprint de scraping: {e}")

try:
    from routes.sentiment_real import sentiment_bp
    app.register_blueprint(sentiment_bp, url_prefix="/api")
    logger.info("Blueprint de análise de sentimentos registrado")
except ImportError as e:
    logger.warning(f"Não foi possível importar blueprint de sentimentos: {e}")

try:
    from routes.backlog import backlog_bp
    app.register_blueprint(backlog_bp, url_prefix="/api")
    logger.info("Blueprint de backlog registrado")
except ImportError as e:
    logger.warning(f"Não foi possível importar blueprint de backlog: {e}")

# Funções auxiliares para autenticação
def is_valid_email(email):
    """Valida se o email tem formato válido"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_jwt_token(email):
    """Gera token JWT para o usuário"""
    payload = {
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_jwt_token(token):
    """Verifica e decodifica token JWT"""
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def log_user_access(email, action="login"):
    """Registra acesso do usuário no log"""
    timestamp = datetime.now(timezone.utc).isoformat()
    log_message = f"[{timestamp}] USER_ACCESS - Email: {email}, Action: {action}"
    logger.info(log_message)
    
    # Também salvar em arquivo específico para auditoria
    try:
        with open('user_access.log', 'a', encoding='utf-8') as f:
            f.write(f"{log_message}\n")
    except Exception as e:
        logger.error(f"Erro ao escrever no arquivo de log: {e}")

# Rotas de autenticação
@app.route("/api/auth/login", methods=["POST"])
def login():
    """
    Endpoint de login que valida email e gera token JWT
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              description: Email do usuário
              example: "usuario@itau.com.br"
          required:
            - email
    responses:
      200:
        description: Login realizado com sucesso
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Login realizado com sucesso"
            token:
              type: string
              description: Token JWT para autenticação
            user:
              type: object
              properties:
                email:
                  type: string
                  example: "usuario@itau.com.br"
      400:
        description: Email inválido ou não fornecido
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Email é obrigatório"
      500:
        description: Erro interno do servidor
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                "success": False,
                "error": "Email é obrigatório"
            }), 400
        
        email = data['email'].strip().lower()
        
        if not is_valid_email(email):
            return jsonify({
                "success": False,
                "error": "Formato de email inválido"
            }), 400
        
        # Registrar acesso no log
        log_user_access(email, "login")
        
        # Gerar token JWT
        token = generate_jwt_token(email)
        
        return jsonify({
            "success": True,
            "message": "Login realizado com sucesso",
            "token": token,
            "user": {
                "email": email
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return jsonify({
            "success": False,
            "error": "Erro interno do servidor"
        }), 500

@app.route("/api/auth/verify", methods=["POST"])
def verify_token():
    """
    Verifica se o token JWT é válido
    ---
    tags:
      - Auth
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Bearer token JWT
    responses:
      200:
        description: Token válido
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            user:
              type: object
              properties:
                email:
                  type: string
                  example: "usuario@itau.com.br"
      401:
        description: Token inválido ou expirado
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Token inválido"
    """
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "success": False,
                "error": "Token não fornecido"
            }), 401
        
        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)
        
        if not payload:
            return jsonify({
                "success": False,
                "error": "Token inválido ou expirado"
            }), 401
        
        return jsonify({
            "success": True,
            "user": {
                "email": payload['email']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na verificação do token: {e}")
        return jsonify({
            "success": False,
            "error": "Erro interno do servidor"
        }), 500

# Rotas da API
@app.route("/api/apps", methods=["GET"])
def get_apps():
    """
    Retorna lista de aplicativos disponíveis
    ---
    tags:
      - Apps
    parameters:
      - name: store
        in: query
        type: string
        enum: [google_play, app_store]
        description: Filtrar por loja
      - name: query
        in: query
        type: string
        required: true
        description: Termo de busca para aplicativos
    responses:
      200:
        description: Lista de aplicativos
        schema:
          type: array
          items:
            $ref: '#/definitions/App'
      500:
        description: Erro interno do servidor
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        store_filter = request.args.get("store")
        search_query = request.args.get("query")
        
        if not search_query:
            return jsonify({"error": "Parâmetro 'query' é obrigatório para buscar aplicativos."}), 400

        apps_list = []
        if store_filter in ["google_play", None]:
            apps_list.extend(google_play_service.search_apps(search_query))
        if store_filter in ["app_store", None]:
            apps_list.extend(apple_store_service.search_apps(search_query))

        return jsonify(apps_list)
    except Exception as e:
        logger.error(f"Erro ao buscar apps: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500

@app.route("/api/apps/<app_id>", methods=["GET"])
def get_app(app_id):
    """
    Retorna detalhes de um aplicativo específico
    ---
    tags:
      - Apps
    parameters:
      - name: app_id
        in: path
        type: string
        required: true
        description: ID único do aplicativo
      - name: store
        in: query
        type: string
        enum: [google_play, app_store]
        required: true
        description: Loja do aplicativo (google_play ou app_store)
    responses:
      200:
        description: Detalhes do aplicativo
        schema:
          $ref: '#/definitions/App'
      404:
        description: App não encontrado
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Erro interno do servidor
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        store = request.args.get("store")
        if not store:
            return jsonify({"error": "Parâmetro 'store' é obrigatório para buscar detalhes do aplicativo."}), 400

        app_details = None
        if store == "google_play":
            app_details = google_play_service.get_app_details(app_id)
        elif store == "app_store":
            app_details = apple_store_service.get_app_details(app_id)

        if not app_details:
            return jsonify({"error": "App não encontrado ou erro ao buscar detalhes."}), 404
        
        return jsonify(app_details)
    except Exception as e:
        logger.error(f"Erro ao buscar app {app_id}: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500

@app.route("/api/apps/<app_id>/reviews", methods=["GET"])
def get_app_reviews(app_id):
    """
    Retorna reviews de um aplicativo
    ---
    tags:
      - Reviews
    parameters:
      - name: app_id
        in: path
        type: string
        required: true
        description: ID único do aplicativo
      - name: store
        in: query
        type: string
        enum: [google_play, app_store]
        required: true
        description: Loja do aplicativo (google_play ou app_store)
      - name: limit
        in: query
        type: integer
        default: 20
        description: Número máximo de reviews a retornar
    responses:
      200:
        description: Lista de reviews
        schema:
          type: array
          items:
            $ref: '#/definitions/Review'
      500:
        description: Erro interno do servidor
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        store = request.args.get("store")
        limit = request.args.get("limit", 20, type=int)
        if not store:
            return jsonify({"error": "Parâmetro 'store' é obrigatório para buscar reviews."}), 400

        reviews_list = []
        if store == "google_play":
            reviews_list, _ = google_play_service.get_app_reviews(app_id, 200)
        elif store == "app_store":
            reviews_list = apple_store_service.get_app_reviews(app_id, 200)

        return jsonify(reviews_list)
    except Exception as e:
        logger.error(f"Erro ao buscar reviews do app {app_id}: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500

@app.route("/api/apps/<app_id>/analysis", methods=["GET"])
def get_app_analysis(app_id):
    """
    Retorna análise de sentimentos do aplicativo
    ---
    tags:
      - Analysis
    parameters:
      - name: app_id
        in: path
        type: string
        required: true
        description: ID único do aplicativo
      - name: store
        in: query
        type: string
        enum: [google_play, app_store]
        required: true
        description: Loja do aplicativo (google_play ou app_store)
      - name: limit
        in: query
        type: integer
        default: 100
        description: Número máximo de reviews para análise
    responses:
      200:
        description: Análise de sentimentos
        schema:
          $ref: '#/definitions/Analysis'
      500:
        description: Erro interno do servidor
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        store = request.args.get("store")
        limit = request.args.get("limit", 100, type=int)
        if not store:
            return jsonify({"error": "Parâmetro 'store' é obrigatório para análise de sentimentos."}), 400

        reviews_data = []
        if store == "google_play":
            reviews_data, _ = google_play_service.get_app_reviews(app_id, count=limit)
        elif store == "app_store":
            reviews_data = apple_store_service.get_app_reviews(app_id, count=limit)

        if not reviews_data:
            return jsonify({
                "total_reviews": 0,
                "positive_percentage": 0,
                "negative_percentage": 0,
                "neutral_percentage": 0,
                "avg_sentiment_score": 0,
                "message": "Nenhuma review encontrada para análise"
            })

        # Realizar análise de sentimentos em tempo real
        analyzed_reviews = sentiment_service.analyze_batch_reviews(reviews_data)
        sentiment_summary = sentiment_service.analyze_app_sentiment_summary(app_id, analyzed_reviews)
        
        return jsonify(sentiment_summary)
    except Exception as e:
        logger.error(f"Erro ao buscar análise do app {app_id}: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500

@app.route("/api/categories", methods=["GET"])
def get_categories():
    """
    Retorna categorias disponíveis (mockadas, pois não há DB)
    ---
    tags:
      - Apps
    responses:
      200:
        description: Lista de categorias
        schema:
          type: array
          items:
            type: string
    """
    return jsonify(["Games", "Education", "Finance", "Social", "Tools", "Health & Fitness"])

@app.route("/api/stores", methods=["GET"])
def get_stores():
    """
    Retorna lojas disponíveis
    ---
    tags:
      - Apps
    responses:
      200:
        description: Lista de lojas
        schema:
          type: array
          items:
            type: string
            enum: [google_play, app_store]
    """
    return jsonify(["google_play", "app_store"])

@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check da API
    ---
    tags:
      - Health
    responses:
      200:
        description: API funcionando corretamente
        schema:
          $ref: '#/definitions/HealthCheck'
      500:
        description: Erro na API
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        return jsonify({
            "status": "healthy",
            "message": "API de Análise de Apps funcionando (sem banco de dados)",
            "version": "3.0.0",
            "database": "disconnected",
            "stats": {
                "total_apps": "N/A",
                "total_reviews": "N/A"
            }
        })
    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        return jsonify({
            "status": "unhealthy",
            "message": "Erro no health check",
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)


from services.backlog_generation_fallback import BacklogGenerationFallbackService


backlog_fallback_service = BacklogGenerationFallbackService()



@app.route("/api/apps/<app_id>/backlog", methods=["GET"])
def get_app_backlog(app_id):
    """
    Gera itens de backlog para um aplicativo baseado em reviews.
    ---
    tags:
      - Backlog
    parameters:
      - name: app_id
        in: path
        type: string
        required: true
        description: ID único do aplicativo
      - name: store
        in: query
        type: string
        enum: [google_play, app_store]
        required: true
        description: Loja do aplicativo (google_play ou app_store)
      - name: limit
        in: query
        type: integer
        default: 100
        description: Número máximo de reviews para usar na geração do backlog
    responses:
      200:
        description: Itens de backlog gerados
        schema:
          type: object
          properties:
            app_name:
              type: string
            total_reviews_processed:
              type: integer
            generated_backlog_items:
              type: array
              items:
                type: object
                properties:
                  type:
                    type: string
                  priority:
                    type: string
                  description:
                    type: string
                  source:
                    type: string
            summary:
              type: string
      500:
        description: Erro interno do servidor
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        store = request.args.get("store")
        limit = request.args.get("limit", 100, type=int)
        if not store:
            return jsonify({"error": "Parâmetro 'store' é obrigatório para gerar backlog."}), 400

        reviews_data = []
        if store == "google_play":
            reviews_data, _ = google_play_service.get_app_reviews(app_id, count=limit)
        elif store == "app_store":
            reviews_data = apple_store_service.get_app_reviews(app_id, count=limit)

        # Aqui você pode adicionar a lógica para tentar a geração de backlog com IA real
        # Se falhar ou não estiver disponível, usa o fallback
        # Por enquanto, vamos direto para o fallback
        backlog_items = backlog_fallback_service.generate_mock_backlog(app_id, reviews_data)
        
        return jsonify(backlog_items)
    except Exception as e:
        logger.error(f"Erro ao gerar backlog para o app {app_id}: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500


