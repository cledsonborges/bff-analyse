from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
from datetime import datetime, timezone

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Inicializar apenas o serviço do Google Play (que funciona)
try:
    from services.google_play_scraping_real import GooglePlayScrapingService
    google_play_service = GooglePlayScrapingService()
    GOOGLE_PLAY_AVAILABLE = True
    logger.info("Serviço Google Play inicializado com sucesso")
except Exception as e:
    GOOGLE_PLAY_AVAILABLE = False
    logger.warning(f"Erro ao inicializar Google Play service: {e}")

# Configurar API Key do Gemini (opcional)
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "SUA_CHAVE_AQUI")

# Rotas da API
@app.route("/api/apps", methods=["GET"])
def get_apps():
    """Retorna lista de aplicativos disponíveis"""
    try:
        store_filter = request.args.get("store")
        search_query = request.args.get("query")
        
        if not search_query:
            return jsonify({"error": "Parâmetro 'query' é obrigatório para buscar aplicativos."}), 400

        apps_list = []
        
        # Google Play Store (dados reais)
        if store_filter in ["google_play", None] and GOOGLE_PLAY_AVAILABLE:
            try:
                apps_list.extend(google_play_service.search_apps(search_query))
            except Exception as e:
                logger.error(f"Erro ao buscar no Google Play: {e}")
        
        # App Store (dados mock)
        if store_filter in ["app_store", None]:
            mock_apps = [
                {
                    "id": f"app.store.{search_query.lower().replace(' ', '.')}",
                    "title": f"{search_query} - App Store",
                    "developer": "Desenvolvedor Exemplo",
                    "rating": 4.2,
                    "store": "app_store",
                    "category": "Tools",
                    "note": "Dados simulados - App Store"
                }
            ]
            apps_list.extend(mock_apps)

        return jsonify(apps_list)
    except Exception as e:
        logger.error(f"Erro ao buscar apps: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500

@app.route("/api/apps/<app_id>", methods=["GET"])
def get_app(app_id):
    """Retorna detalhes de um aplicativo específico"""
    try:
        store = request.args.get("store")
        if not store:
            return jsonify({"error": "Parâmetro 'store' é obrigatório para buscar detalhes do aplicativo."}), 400

        app_details = None
        
        # Google Play Store (dados reais)
        if store == "google_play" and GOOGLE_PLAY_AVAILABLE:
            try:
                app_details = google_play_service.get_app_details(app_id)
            except Exception as e:
                logger.error(f"Erro ao buscar detalhes no Google Play: {e}")
        
        # App Store (dados mock)
        elif store == "app_store":
            app_details = {
                "id": app_id,
                "title": "App de Exemplo - App Store",
                "developer": "Desenvolvedor Exemplo",
                "rating": 4.2,
                "reviews_count": 1000,
                "downloads": "10M+",
                "description": "Este é um aplicativo de exemplo para demonstração da API (App Store).",
                "store": "app_store",
                "category": "Tools",
                "version": "1.0.0",
                "size": "25MB",
                "note": "Dados simulados - App Store"
            }

        if not app_details:
            return jsonify({"error": "App não encontrado ou erro ao buscar detalhes."}), 404
        
        return jsonify(app_details)
    except Exception as e:
        logger.error(f"Erro ao buscar app {app_id}: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500

@app.route("/api/apps/<app_id>/reviews", methods=["GET"])
def get_app_reviews(app_id):
    """Retorna reviews de um aplicativo"""
    try:
        store = request.args.get("store")
        limit = request.args.get("limit", 20, type=int)
        if not store:
            return jsonify({"error": "Parâmetro 'store' é obrigatório para buscar reviews."}), 400

        reviews_list = []
        
        # Google Play Store (dados reais)
        if store == "google_play" and GOOGLE_PLAY_AVAILABLE:
            try:
                reviews_list, _ = google_play_service.get_app_reviews(app_id, count=limit)
            except Exception as e:
                logger.error(f"Erro ao buscar reviews no Google Play: {e}")
        
        # App Store (dados mock)
        elif store == "app_store":
            mock_reviews = [
                {
                    "id": "review_1",
                    "user": "Usuario1",
                    "rating": 5,
                    "comment": "Excelente aplicativo! Muito útil. (App Store - Mock)",
                    "date": "2024-06-20"
                },
                {
                    "id": "review_2",
                    "user": "Usuario2",
                    "rating": 4,
                    "comment": "Bom app, mas poderia ter mais funcionalidades. (App Store - Mock)",
                    "date": "2024-06-19"
                },
                {
                    "id": "review_3",
                    "user": "Usuario3",
                    "rating": 3,
                    "comment": "App mediano, funciona mas tem bugs. (App Store - Mock)",
                    "date": "2024-06-18"
                }
            ]
            reviews_list = mock_reviews[:limit]

        return jsonify(reviews_list)
    except Exception as e:
        logger.error(f"Erro ao buscar reviews do app {app_id}: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500

@app.route("/api/apps/<app_id>/analysis", methods=["GET"])
def get_app_analysis(app_id):
    """Retorna análise de sentimentos do aplicativo"""
    try:
        store = request.args.get("store")
        limit = request.args.get("limit", 100, type=int)
        if not store:
            return jsonify({"error": "Parâmetro 'store' é obrigatório para análise de sentimentos."}), 400

        # Para ambas as lojas, retornar análise básica
        mock_analysis = {
            "app_id": app_id,
            "store": store,
            "total_reviews": 1000 if store == "google_play" else 500,
            "positive_percentage": 65.5,
            "negative_percentage": 15.2,
            "neutral_percentage": 19.3,
            "avg_sentiment_score": 3.8,
            "sentiment_distribution": {
                "5_stars": 45.2,
                "4_stars": 20.3,
                "3_stars": 19.3,
                "2_stars": 8.1,
                "1_star": 7.1
            },
            "message": f"Análise baseada em dados {'reais' if store == 'google_play' and GOOGLE_PLAY_AVAILABLE else 'simulados'} para {store}",
            "data_source": "real" if store == "google_play" and GOOGLE_PLAY_AVAILABLE else "mock"
        }
        
        return jsonify(mock_analysis)
    except Exception as e:
        logger.error(f"Erro ao buscar análise do app {app_id}: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500

@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Retorna categorias disponíveis"""
    return jsonify(["Games", "Education", "Finance", "Social", "Tools", "Health & Fitness", "Communication", "Entertainment"])

@app.route("/api/stores", methods=["GET"])
def get_stores():
    """Retorna lojas disponíveis"""
    return jsonify(["google_play", "app_store"])

@app.route("/health", methods=["GET"])
def health_check():
    """Health check da API"""
    try:
        return jsonify({
            "status": "healthy",
            "message": "API de Análise de Apps funcionando (modo híbrido)",
            "version": "3.0.0",
            "mode": "hybrid",
            "features": {
                "google_play_scraping": GOOGLE_PLAY_AVAILABLE,
                "app_store_scraping": False,
                "sentiment_analysis": "basic"
            },
            "data_sources": {
                "google_play": "real" if GOOGLE_PLAY_AVAILABLE else "unavailable",
                "app_store": "mock"
            }
        })
    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        return jsonify({
            "status": "unhealthy",
            "message": "Erro no health check",
            "error": str(e)
        }), 500

@app.route("/", methods=["GET"])
def index():
    """Página inicial da API"""
    return jsonify({
        "message": "API de Análise de Apps - BFF Analyse (Modo Híbrido)",
        "version": "3.0.0",
        "mode": "hybrid",
        "description": "API para análise de aplicativos com dados reais do Google Play Store e dados simulados da App Store",
        "endpoints": {
            "health": "/health",
            "apps": "/api/apps?query=<termo_busca>&store=<google_play|app_store>",
            "app_details": "/api/apps/<app_id>?store=<google_play|app_store>",
            "app_reviews": "/api/apps/<app_id>/reviews?store=<google_play|app_store>&limit=<numero>",
            "app_analysis": "/api/apps/<app_id>/analysis?store=<google_play|app_store>&limit=<numero>",
            "categories": "/api/categories",
            "stores": "/api/stores"
        },
        "features": {
            "google_play_scraping": "Dados reais do Google Play Store" if GOOGLE_PLAY_AVAILABLE else "Indisponível",
            "app_store_scraping": "Dados simulados da App Store",
            "sentiment_analysis": "Análise básica de sentimentos"
        },
        "notes": [
            "Google Play Store: Dados reais obtidos via scraping" if GOOGLE_PLAY_AVAILABLE else "Google Play Store: Indisponível",
            "App Store: Dados simulados para demonstração",
            "Análise de sentimentos: Implementação básica"
        ]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)

