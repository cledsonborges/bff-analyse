import os
from flask import Blueprint, jsonify, request
from services.sentiment_analysis_real import SentimentAnalysisService
from models import db, App, Review, AnalysisReport
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

sentiment_bp = Blueprint("sentiment", __name__)

# Inicializar serviço de análise de sentimentos
sentiment_service = SentimentAnalysisService(api_key=os.getenv("GEMINI_API_KEY"))

@sentiment_bp.route("/sentiment/analyze-app/<app_id>", methods=["POST"])
def analyze_app_sentiment(app_id):
    """Analisa sentimentos de todas as reviews de um aplicativo"""
    try:
        data = request.get_json() or {}
        force_reanalysis = data.get("force_reanalysis", False)
        limit = data.get("limit", 100)  # Limitar número de reviews para análise
        
        # Verificar se app existe
        app = App.query.filter_by(app_id=app_id).first()
        if not app:
            return jsonify({"error": "App não encontrado"}), 404
        
        # Buscar reviews que ainda não foram analisadas ou forçar reanálise
        if force_reanalysis:
            reviews = Review.query.filter_by(app_id=app_id).limit(limit).all()
        else:
            reviews = Review.query.filter_by(app_id=app_id).filter(
                (Review.sentiment == None) | (Review.sentiment == "")
            ).limit(limit).all()
        
        if not reviews:
            return jsonify({
                "message": "Nenhuma review encontrada para análise",
                "app_id": app_id,
                "total_reviews": 0
            })
        
        logger.info(f"Analisando {len(reviews)} reviews do app {app.name}")
        
        # Preparar dados para análise
        reviews_data = []
        for review in reviews:
            reviews_data.append({
                "id": review.id,
                "content": review.content
            })
        
        # Analisar sentimentos
        analysis_results = sentiment_service.analyze_batch_reviews(reviews_data)
        
        # Atualizar reviews no banco
        updated_count = 0
        for result in analysis_results:
            review = Review.query.get(result["review_id"])
            if review:
                review.sentiment = result["sentiment"]
                review.sentiment_score = result["sentiment_score"]
                updated_count += 1
        
        # Gerar relatório de análise
        all_reviews = Review.query.filter_by(app_id=app_id).all()
        reviews_summary = []
        for review in all_reviews:
            if review.sentiment:
                reviews_summary.append({
                    "sentiment": review.sentiment,
                    "content": review.content,
                    "rating": review.rating
                })
        
        app_summary = sentiment_service.analyze_app_sentiment_summary(app.name, reviews_summary)
        
        # Salvar relatório no banco
        existing_report = AnalysisReport.query.filter_by(app_id=app_id).first()
        if existing_report:
            # Atualizar relatório existente
            existing_report.total_reviews = app_summary["total_reviews"]
            existing_report.positive_count = int(app_summary["positive_percentage"] * app_summary["total_reviews"] / 100)
            existing_report.negative_count = int(app_summary["negative_percentage"] * app_summary["total_reviews"] / 100)
            existing_report.neutral_count = int(app_summary["neutral_percentage"] * app_summary["total_reviews"] / 100)
            existing_report.avg_sentiment_score = app_summary.get("confidence", 0.5)
            existing_report.main_issues = json.dumps(app_summary.get("main_issues", []))
            existing_report.created_at = datetime.now(timezone.utc)
        else:
            # Criar novo relatório
            new_report = AnalysisReport(
                app_id=app_id,
                total_reviews=app_summary["total_reviews"],
                positive_count=int(app_summary["positive_percentage"] * app_summary["total_reviews"] / 100),
                negative_count=int(app_summary["negative_percentage"] * app_summary["total_reviews"] / 100),
                neutral_count=int(app_summary["neutral_percentage"] * app_summary["total_reviews"] / 100),
                avg_sentiment_score=app_summary.get("confidence", 0.5),
                main_issues=json.dumps(app_summary.get("main_issues", []))
            )
            db.session.add(new_report)
        
        db.session.commit()
        
        return jsonify({
            "message": "Análise de sentimentos concluída",
            "app_id": app_id,
            "app_name": app.name,
            "reviews_analyzed": len(reviews),
            "reviews_updated": updated_count,
            "summary": app_summary
        })
        
    except Exception as e:
        logger.error(f"Erro na análise de sentimentos do app {app_id}: {e}")
        db.session.rollback()
        return jsonify({"error": "Erro interno do servidor"}), 500

@sentiment_bp.route("/sentiment/analyze-review", methods=["POST"])
def analyze_single_review():
    """Analisa o sentimento de uma review específica"""
    try:
        data = request.get_json()
        if not data or "content" not in data:
            return jsonify({"error": "Conteúdo da review é obrigatório"}), 400
        
        content = data["content"]
        review_id = data.get("review_id")
        
        # Analisar sentimento
        analysis = sentiment_service.analyze_single_review(content)
        
        # Se review_id foi fornecido, atualizar no banco
        if review_id:
            review = Review.query.get(review_id)
            if review:
                review.sentiment = analysis["sentiment"]
                review.sentiment_score = analysis["score"]
                db.session.commit()
        
        return jsonify({
            "sentiment": analysis["sentiment"],
            "sentiment_score": analysis["score"],
            "reasoning": analysis.get("reasoning", ""),
            "review_id": review_id
        })
        
    except Exception as e:
        logger.error(f"Erro na análise de review: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@sentiment_bp.route("/sentiment/batch-analyze", methods=["POST"])
def batch_analyze_apps():
    """Analisa sentimentos de múltiplos aplicativos"""
    try:
        data = request.get_json() or {}
        app_ids = data.get("app_ids", [])
        limit_per_app = data.get("limit_per_app", 50)
        
        if not app_ids:
            # Se não especificado, analisar todos os apps com reviews não analisadas
            apps_with_unanalyzed = db.session.query(App.app_id).join(Review).filter(
                (Review.sentiment == None) | (Review.sentiment == "")
            ).distinct().limit(10).all()
            app_ids = [app[0] for app in apps_with_unanalyzed]
        
        if not app_ids:
            return jsonify({
                "message": "Nenhum app encontrado para análise",
                "apps_analyzed": 0
            })
        
        results = []
        
        for app_id in app_ids:
            try:
                logger.info(f"Analisando app: {app_id}")
                
                # Analisar app
                app = App.query.filter_by(app_id=app_id).first()
                if not app:
                    continue
                
                # Buscar reviews não analisadas
                reviews = Review.query.filter_by(app_id=app_id).filter(
                    (Review.sentiment == None) | (Review.sentiment == "")
                ).limit(limit_per_app).all()
                
                if not reviews:
                    continue
                
                # Preparar dados para análise
                reviews_data = [{"id": r.id, "content": r.content} for r in reviews]
                
                # Analisar sentimentos
                analysis_results = sentiment_service.analyze_batch_reviews(reviews_data)
                
                # Atualizar reviews
                updated_count = 0
                for result in analysis_results:
                    review = Review.query.get(result["review_id"])
                    if review:
                        review.sentiment = result["sentiment"]
                        review.sentiment_score = result["sentiment_score"]
                        updated_count += 1
                
                results.append({
                    "app_id": app_id,
                    "app_name": app.name,
                    "reviews_analyzed": len(reviews),
                    "reviews_updated": updated_count
                })
                
            except Exception as e:
                logger.error(f"Erro ao analisar app {app_id}: {e}")
                continue
        
        db.session.commit()
        
        return jsonify({
            "message": "Análise em lote concluída",
            "apps_analyzed": len(results),
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Erro na análise em lote: {e}")
        db.session.rollback()
        return jsonify({"error": "Erro interno do servidor"}), 500

@sentiment_bp.route("/sentiment/stats", methods=["GET"])
def get_sentiment_stats():
    """Retorna estatísticas gerais de análise de sentimentos"""
    try:
        # Estatísticas gerais
        total_reviews = Review.query.count()
        analyzed_reviews = Review.query.filter(Review.sentiment != None).filter(Review.sentiment != "").count()
        
        # Contagem por sentimento
        positive_count = Review.query.filter(Review.sentiment == "positive").count()
        negative_count = Review.query.filter(Review.sentiment == "negative").count()
        neutral_count = Review.query.filter(Review.sentiment == "neutral").count()
        
        # Apps com análises
        apps_with_analysis = db.session.query(App.app_id).join(Review).filter(
            Review.sentiment != None
        ).distinct().count()
        
        total_apps = App.query.count()
        
        return jsonify({
            "total_reviews": total_reviews,
            "analyzed_reviews": analyzed_reviews,
            "unanalyzed_reviews": total_reviews - analyzed_reviews,
            "analysis_percentage": round((analyzed_reviews / total_reviews) * 100, 1) if total_reviews > 0 else 0,
            "sentiment_distribution": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count
            },
            "apps_stats": {
                "total_apps": total_apps,
                "apps_with_analysis": apps_with_analysis,
                "apps_without_analysis": total_apps - apps_with_analysis
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@sentiment_bp.route("/sentiment/config", methods=["GET"])
def get_sentiment_config():
    """Retorna configuração do serviço de análise de sentimentos"""
    return jsonify({
        "service_available": not sentiment_service.use_mock,
        "using_mock": sentiment_service.use_mock,
        "api_configured": sentiment_service.api_key is not None,
        "message": "Serviço Gemini configurado" if not sentiment_service.use_mock else "Usando análise mock - configure GEMINI_API_KEY"
    })


