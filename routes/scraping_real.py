from flask import Blueprint, jsonify, request
from services.google_play_scraping_real import GooglePlayScrapingService
from services.apple_store_scraping_real import AppleAppStoreScrapingService
import logging

logger = logging.getLogger(__name__)

scraping_bp = Blueprint("scraping", __name__)

# Inicializar serviços
google_play_service = GooglePlayScrapingService()
apple_store_service = AppleAppStoreScrapingService()

@scraping_bp.route("/scraping/search", methods=["POST"])
def search_apps():
    """Busca aplicativos nas lojas e retorna os resultados"""
    try:
        data = request.get_json()
        query = data.get("query", "")
        store = data.get("store", "both")  # "google_play", "app_store", "both"
        limit = data.get("limit", 10)
        
        if not query:
            return jsonify({"error": "Query é obrigatória"}), 400
        
        results = []
        
        # Buscar no Google Play
        if store in ["google_play", "both"]:
            logger.info(f"Buscando no Google Play: {query}")
            google_results = google_play_service.search_apps(query, limit)
            results.extend(google_results)
        
        # Buscar na App Store
        if store in ["app_store", "both"]:
            logger.info(f"Buscando na App Store: {query}")
            apple_results = apple_store_service.search_apps(query, limit)
            results.extend(apple_results)
        
        return jsonify({
            "message": f"Busca realizada com sucesso",
            "query": query,
            "total_found": len(results),
            "apps": results
        })
        
    except Exception as e:
        logger.error(f"Erro na busca de apps: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@scraping_bp.route("/scraping/app/<app_id>/details", methods=["GET"])
def get_app_details_route(app_id):
    """Retorna detalhes completos de um aplicativo"""
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
        logger.error(f"Erro ao buscar detalhes do app {app_id}: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@scraping_bp.route("/scraping/app/<app_id>/reviews", methods=["GET"])
def get_app_reviews_route(app_id):
    """Retorna reviews de um aplicativo"""
    try:
        store = request.args.get("store")
        limit = request.args.get("limit", 20, type=int)
        if not store:
            return jsonify({"error": "Parâmetro 'store' é obrigatório para buscar reviews."}), 400

        reviews_list = []
        if store == "google_play":
            reviews_list = google_play_service.get_app_reviews(app_id, count=limit)
        elif store == "app_store":
            reviews_list = apple_store_service.get_app_reviews(app_id, limit=limit)

        return jsonify(reviews_list)
    except Exception as e:
        logger.error(f"Erro ao buscar reviews do app {app_id}: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@scraping_bp.route("/scraping/popular", methods=["GET"])
def get_popular_apps_route():
    """Retorna apps populares de diferentes categorias"""
    try:
        categories = request.args.get("categories", "communication,social,entertainment").split(",")
        limit_per_category = request.args.get("limit_per_category", 10, type=int)
        
        all_results = []
        
        for category in categories:
            logger.info(f"Coletando apps populares da categoria: {category}")
            
            # Google Play
            google_apps = google_play_service.get_popular_apps_by_category(category, limit_per_category)
            all_results.extend(google_apps)
            
            # App Store
            apple_apps = apple_store_service.get_popular_apps_by_category(category, limit_per_category)
            all_results.extend(apple_apps)
        
        return jsonify({
            "message": "Apps populares coletados com sucesso",
            "categories": categories,
            "total_apps": len(all_results),
            "apps": all_results
        })
        
    except Exception as e:
        logger.error(f"Erro ao coletar apps populares: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


