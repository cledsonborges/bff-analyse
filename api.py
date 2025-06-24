from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
from datetime import datetime, timezone
from flasgger import swag_from
from swagger_config import init_swagger

# Importar serviços de scraping e análise de sentimentos
from services.google_play_scraping_real import GooglePlayScrapingService
from services.apple_store_scraping_real import AppleAppStoreScrapingService
from services.sentiment_analysis_real import SentimentAnalysisService

# Configurar API Key do Gemini
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "SUA_CHAVE_AQUI")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

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
            reviews_list = google_play_service.get_app_reviews(app_id, limit=limit)
        elif store == "app_store":
            reviews_list = apple_store_service.get_app_reviews(app_id, limit=limit)

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
            reviews_data = google_play_service.get_app_reviews(app_id, limit=limit)
        elif store == "app_store":
            reviews_data = apple_store_service.get_app_reviews(app_id, limit=limit)

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
    app.run(host="0.0.0.0", port=5002, debug=True)

