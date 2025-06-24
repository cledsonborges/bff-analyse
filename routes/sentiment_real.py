import os
from flask import Blueprint, jsonify, request
from services.sentiment_analysis_real import SentimentAnalysisService
import logging
import json

logger = logging.getLogger(__name__)

sentiment_bp = Blueprint("sentiment", __name__)

# Inicializar serviço de análise de sentimentos
sentiment_service = SentimentAnalysisService(api_key=os.getenv("GEMINI_API_KEY"))

@sentiment_bp.route("/sentiment/analyze-reviews", methods=["POST"])
def analyze_reviews():
    """Analisa sentimentos de uma lista de reviews fornecida"""
    try:
        data = request.get_json()
        reviews_data = data.get("reviews", [])
        app_name = data.get("app_name", "Aplicativo Desconhecido")

        if not reviews_data:
            return jsonify({"error": "Nenhuma review fornecida para análise."}), 400

        logger.info(f"Analisando {len(reviews_data)} reviews para {app_name}")
        
        # Analisar sentimentos em lote
        analyzed_reviews = sentiment_service.analyze_batch_reviews(reviews_data)
        sentiment_summary = sentiment_service.analyze_app_sentiment_summary(app_name, analyzed_reviews)
        
        return jsonify({
            "message": "Análise de sentimentos concluída",
            "app_name": app_name,
            "reviews_analyzed": len(analyzed_reviews),
            "summary": sentiment_summary,
            "analyzed_reviews_list": analyzed_reviews
        })
        
    except Exception as e:
        logger.error(f"Erro na análise de sentimentos: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500

@sentiment_bp.route("/sentiment/analyze-single-review", methods=["POST"])
def analyze_single_review_route():
    """Analisa o sentimento de uma única review específica"""
    try:
        data = request.get_json()
        if not data or "content" not in data:
            return jsonify({"error": "Conteúdo da review é obrigatório"}), 400
        
        content = data["content"]
        
        # Analisar sentimento
        analysis = sentiment_service.analyze_single_review(content)
        
        return jsonify({
            "sentiment": analysis["sentiment"],
            "sentiment_score": analysis["score"],
            "reasoning": analysis.get("reasoning", "")
        })
        
    except Exception as e:
        logger.error(f"Erro na análise de review: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@sentiment_bp.route("/sentiment/config", methods=["GET"])
def get_sentiment_config():
    """Retorna configuração do serviço de análise de sentimentos"""
    return jsonify({
        "service_available": not sentiment_service.use_fallback,
        "using_fallback": sentiment_service.use_fallback,
        "message": "Serviço Gemini configurado" if not sentiment_service.use_fallback else "Usando análise básica - configure GEMINI_API_KEY para análise avançada"
    })


