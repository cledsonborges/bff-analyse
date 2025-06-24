from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import logging
from models import db, App, Review, AnalysisReport
import os
from datetime import datetime, timezone

# Configurar API Key do Gemini
os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY', 'SUA_CHAVE_AQUI')


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuração do banco de dados
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app_analysis.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar banco de dados
db.init_app(app)

# Criar tabelas
with app.app_context():
    db.create_all()
    logger.info("Banco de dados inicializado")

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
    from routes.code_buddy_agent import code_buddy_bp
    app.register_blueprint(code_buddy_bp, url_prefix="/api")
    logger.info("Blueprint do agente Code Buddy registrado")
except ImportError as e:
    logger.warning(f"Erro ao importar blueprint do Code Buddy: {e}")    
    

# Função para popular dados iniciais
def populate_initial_data():
    # Não popular dados iniciais, pois serão coletados via scraping
    pass

# Popular dados na inicialização
with app.app_context():
    populate_initial_data()

# Rotas da API
@app.route("/api/apps", methods=["GET"])
def get_apps():
    """Retorna lista de aplicativos disponíveis"""
    try:
        store_filter = request.args.get("store")  # Filtrar por loja
        category_filter = request.args.get("category")  # Filtrar por categoria
        
        query = App.query
        
        if store_filter:
            query = query.filter(App.store == store_filter)
        
        if category_filter:
            query = query.filter(App.category.ilike(f"%{category_filter}%"))
        
        apps = query.all()
        apps_list = []
        for app in apps:
            apps_list.append({
                "app_id": app.app_id,
                "name": app.name,
                "store": app.store,
                "current_version": app.current_version,
                "rating": app.rating,
                "total_reviews": app.total_reviews,
                "category": app.category,
                "icon_url": app.icon_url,
                "last_updated": app.last_updated.isoformat() if app.last_updated else None
            })
        return jsonify(apps_list)
    except Exception as e:
        logger.error(f"Erro ao buscar apps: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route("/api/apps/<app_id>", methods=["GET"])
def get_app(app_id):
    """Retorna detalhes de um aplicativo específico"""
    try:
        app = App.query.filter_by(app_id=app_id).first()
        if not app:
            return jsonify({"error": "App não encontrado"}), 404
        
        return jsonify({
            "app_id": app.app_id,
            "name": app.name,
            "store": app.store,
            "current_version": app.current_version,
            "rating": app.rating,
            "total_reviews": app.total_reviews,
            "category": app.category,
            "description": app.description,
            "icon_url": app.icon_url,
            "last_updated": app.last_updated.isoformat() if app.last_updated else None
        })
    except Exception as e:
        logger.error(f"Erro ao buscar app {app_id}: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route("/api/apps/<app_id>/reviews", methods=["GET"])
def get_app_reviews(app_id):
    """Retorna reviews de um aplicativo"""
    try:
        limit = request.args.get("limit", 20, type=int)
        sentiment_filter = request.args.get("sentiment")  # Filtrar por sentimento
        
        query = Review.query.filter_by(app_id=app_id)
        
        if sentiment_filter:
            query = query.filter(Review.sentiment == sentiment_filter)
        
        reviews = query.order_by(Review.date.desc()).limit(limit).all()
        
        reviews_list = []
        for review in reviews:
            reviews_list.append({
                "id": review.id,
                "user_name": review.user_name,
                "content": review.content,
                "rating": review.rating,
                "sentiment": review.sentiment,
                "sentiment_score": review.sentiment_score,
                "date": review.date.isoformat() if review.date else None
            })
        
        return jsonify(reviews_list)
    except Exception as e:
        logger.error(f"Erro ao buscar reviews do app {app_id}: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route("/api/apps/<app_id>/analysis", methods=["GET"])
def get_app_analysis(app_id):
    """Retorna análise de sentimentos do aplicativo"""
    try:
        # Buscar relatório mais recente
        report = AnalysisReport.query.filter_by(app_id=app_id).order_by(AnalysisReport.created_at.desc()).first()
        
        if not report:
            # Se não há relatório, calcular em tempo real
            reviews = Review.query.filter_by(app_id=app_id).all()
            if not reviews:
                return jsonify({
                    "total_reviews": 0,
                    "positive_percentage": 0,
                    "negative_percentage": 0,
                    "neutral_percentage": 0,
                    "avg_sentiment_score": 0,
                    "message": "Nenhuma review encontrada"
                })
            
            positive = len([r for r in reviews if r.sentiment == "positive"])
            negative = len([r for r in reviews if r.sentiment == "negative"])
            neutral = len([r for r in reviews if r.sentiment == "neutral"])
            total = len(reviews)
            
            return jsonify({
                "total_reviews": total,
                "positive_percentage": round((positive / total) * 100, 1),
                "negative_percentage": round((negative / total) * 100, 1),
                "neutral_percentage": round((neutral / total) * 100, 1),
                "avg_sentiment_score": sum([r.sentiment_score or 0 for r in reviews]) / total if total > 0 else 0,
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
        
        total = report.positive_count + report.negative_count + report.neutral_count
        return jsonify({
            "total_reviews": total,
            "positive_percentage": round((report.positive_count / total) * 100, 1) if total > 0 else 0,
            "negative_percentage": round((report.negative_count / total) * 100, 1) if total > 0 else 0,
            "neutral_percentage": round((report.neutral_count / total) * 100, 1) if total > 0 else 0,
            "avg_sentiment_score": report.avg_sentiment_score,
            "last_updated": report.created_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar análise do app {app_id}: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Retorna categorias disponíveis"""
    try:
        categories = db.session.query(App.category).distinct().all()
        category_list = [cat[0] for cat in categories if cat[0]]
        return jsonify(category_list)
    except Exception as e:
        logger.error(f"Erro ao buscar categorias: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@app.route("/api/stores", methods=["GET"])
def get_stores():
    """Retorna lojas disponíveis"""
    return jsonify(["google_play", "app_store"])

@app.route("/health", methods=["GET"])
def health_check():
    """Health check da API"""
    try:
        # Testar conexão com banco
        db.session.execute(text("SELECT 1"))
        app_count = App.query.count()
        review_count = Review.query.count()
        
        return jsonify({
            "status": "healthy",
            "message": "API de Análise de Apps funcionando",
            "version": "3.0.0",
            "database": "connected",
            "stats": {
                "total_apps": app_count,
                "total_reviews": review_count
            }
        })
    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        return jsonify({
            "status": "unhealthy",
            "message": "Erro na conexão com banco de dados",
            "error": str(e)
        }), 500

if __name__ == "__main__":
    with app.app_context():
        populate_initial_data()
    app.run(host="0.0.0.0", port=5002, debug=True)
