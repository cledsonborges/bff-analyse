from flask import Blueprint, jsonify, request
from services.google_play_scraping_real import GooglePlayScrapingService
from services.apple_store_scraping_real import AppleAppStoreScrapingService
from models import db, App, Review
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

scraping_bp = Blueprint('scraping', __name__)

# Inicializar serviços
google_play_service = GooglePlayScrapingService()
apple_store_service = AppleAppStoreScrapingService()

@scraping_bp.route('/scraping/search', methods=['POST'])
def search_apps():
    """Busca aplicativos nas lojas e adiciona ao banco"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        store = data.get('store', 'both')  # 'google_play', 'app_store', 'both'
        limit = data.get('limit', 10)
        
        if not query:
            return jsonify({'error': 'Query é obrigatória'}), 400
        
        results = []
        
        # Buscar no Google Play
        if store in ['google_play', 'both']:
            logger.info(f"Buscando no Google Play: {query}")
            google_results = google_play_service.search_apps(query, limit)
            
            for app_data in google_results:
                # Verificar se app já existe
                existing_app = App.query.filter_by(app_id=app_data['app_id']).first()
                
                if not existing_app:
                    # Criar novo app
                    new_app = App(
                        app_id=app_data['app_id'],
                        name=app_data['name'],
                        store=app_data['store'],
                        category=app_data['category'],
                        rating=app_data['rating'],
                        icon_url=app_data['icon_url'],
                        description=app_data['description']
                    )
                    db.session.add(new_app)
                    logger.info(f"Adicionado app: {app_data['name']}")
                
                results.append(app_data)
        
        # Buscar na App Store
        if store in ['app_store', 'both']:
            logger.info(f"Buscando na App Store: {query}")
            apple_results = apple_store_service.search_apps(query, limit)
            
            for app_data in apple_results:
                # Verificar se app já existe
                existing_app = App.query.filter_by(app_id=app_data['app_id']).first()
                
                if not existing_app:
                    # Criar novo app
                    new_app = App(
                        app_id=app_data['app_id'],
                        name=app_data['name'],
                        store=app_data['store'],
                        category=app_data['category'],
                        rating=app_data['rating'],
                        total_reviews=app_data['total_reviews'],
                        icon_url=app_data['icon_url'],
                        description=app_data['description'],
                        current_version=app_data['current_version']
                    )
                    db.session.add(new_app)
                    logger.info(f"Adicionado app: {app_data['name']}")
                
                results.append(app_data)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Busca realizada com sucesso',
            'query': query,
            'total_found': len(results),
            'apps': results
        })
        
    except Exception as e:
        logger.error(f"Erro na busca de apps: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@scraping_bp.route('/scraping/app/<app_id>/details', methods=['POST'])
def update_app_details(app_id):
    """Atualiza detalhes completos de um aplicativo"""
    try:
        app = App.query.filter_by(app_id=app_id).first()
        if not app:
            return jsonify({'error': 'App não encontrado'}), 404
        
        # Obter detalhes atualizados
        if app.store == 'google_play':
            app_data = google_play_service.get_app_details(app_id)
        elif app.store == 'app_store':
            app_data = apple_store_service.get_app_details(app_id)
        else:
            return jsonify({'error': 'Loja não suportada'}), 400
        
        if not app_data:
            return jsonify({'error': 'Não foi possível obter detalhes do app'}), 500
        
        # Atualizar dados do app
        app.name = app_data.get('name', app.name)
        app.current_version = app_data.get('current_version', app.current_version)
        app.rating = app_data.get('rating', app.rating)
        app.total_reviews = app_data.get('total_reviews', app.total_reviews)
        app.category = app_data.get('category', app.category)
        app.description = app_data.get('description', app.description)
        app.icon_url = app_data.get('icon_url', app.icon_url)
        app.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Detalhes do app atualizados com sucesso',
            'app': {
                'app_id': app.app_id,
                'name': app.name,
                'store': app.store,
                'current_version': app.current_version,
                'rating': app.rating,
                'total_reviews': app.total_reviews,
                'category': app.category,
                'last_updated': app.last_updated.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao atualizar detalhes do app {app_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@scraping_bp.route('/scraping/app/<app_id>/reviews', methods=['POST'])
def collect_app_reviews(app_id):
    """Coleta reviews de um aplicativo"""
    try:
        data = request.get_json() or {}
        count = data.get('count', 100)
        
        app = App.query.filter_by(app_id=app_id).first()
        if not app:
            return jsonify({'error': 'App não encontrado'}), 404
        
        # Coletar reviews
        if app.store == 'google_play':
            reviews_data, continuation_token = google_play_service.get_app_reviews(app_id, count)
        elif app.store == 'app_store':
            reviews_data = apple_store_service.get_app_reviews(app_id, count)
            continuation_token = None
        else:
            return jsonify({'error': 'Loja não suportada'}), 400
        
        # Salvar reviews no banco
        new_reviews = 0
        for review_data in reviews_data:
            # Verificar se review já existe
            existing_review = Review.query.filter_by(
                app_id=app_id,
                review_id=review_data.get('review_id', '')
            ).first()
            
            if not existing_review and review_data.get('content'):
                new_review = Review(
                    app_id=app_id,
                    review_id=review_data.get('review_id', ''),
                    user_name=review_data.get('user_name', 'Usuário Anônimo'),
                    content=review_data.get('content', ''),
                    rating=review_data.get('rating', 0),
                    date=review_data.get('date', datetime.utcnow())
                )
                db.session.add(new_review)
                new_reviews += 1
        
        db.session.commit()
        
        return jsonify({
            'message': 'Reviews coletadas com sucesso',
            'app_id': app_id,
            'total_collected': len(reviews_data),
            'new_reviews': new_reviews,
            'continuation_token': continuation_token
        })
        
    except Exception as e:
        logger.error(f"Erro ao coletar reviews do app {app_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@scraping_bp.route('/scraping/popular', methods=['POST'])
def collect_popular_apps():
    """Coleta apps populares de diferentes categorias"""
    try:
        data = request.get_json() or {}
        categories = data.get('categories', ['communication', 'social', 'entertainment'])
        limit_per_category = data.get('limit_per_category', 10)
        
        all_results = []
        
        for category in categories:
            logger.info(f"Coletando apps populares da categoria: {category}")
            
            # Google Play
            google_apps = google_play_service.get_popular_apps_by_category(category, limit_per_category)
            
            # App Store
            apple_apps = apple_store_service.get_popular_apps_by_category(category, limit_per_category)
            
            category_apps = google_apps + apple_apps
            
            # Salvar no banco
            for app_data in category_apps:
                existing_app = App.query.filter_by(app_id=app_data['app_id']).first()
                
                if not existing_app:
                    new_app = App(
                        app_id=app_data['app_id'],
                        name=app_data['name'],
                        store=app_data['store'],
                        category=app_data['category'],
                        rating=app_data.get('rating', 0),
                        total_reviews=app_data.get('total_reviews', 0),
                        icon_url=app_data.get('icon_url', ''),
                        description=app_data.get('description', ''),
                        current_version=app_data.get('current_version', '')
                    )
                    db.session.add(new_app)
            
            all_results.extend(category_apps)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Apps populares coletados com sucesso',
            'categories': categories,
            'total_apps': len(all_results),
            'apps_by_category': {cat: len([a for a in all_results if a.get('category', '').lower().find(cat) >= 0]) for cat in categories}
        })
        
    except Exception as e:
        logger.error(f"Erro ao coletar apps populares: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

