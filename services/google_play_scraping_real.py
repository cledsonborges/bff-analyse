import logging
from google_play_scraper import app, reviews, Sort, search
from datetime import datetime, timezone
import time
import random

logger = logging.getLogger(__name__)

class GooglePlayScrapingService:
    def __init__(self):
        self.delay_range = (1, 3)  # Delay entre requests para evitar rate limiting
    
    def search_apps(self, query, limit=10):
        """Busca aplicativos no Google Play Store"""
        try:
            logger.info(f"Buscando apps no Google Play: {query}")
            results = search(query, lang='pt', country='br', n_hits=limit)
            apps_data = []
            for result in results:
                app_data = {
                    'app_id': result['appId'],
                    'name': result['title'],
                    'store': 'google_play',
                    'category': result.get('genre', ''),
                    'rating': result.get('score', 0),
                    'icon_url': result.get('icon', ''),
                    'description': result.get('summary', '')
                }
                apps_data.append(app_data)
                
            logger.info(f"Encontrados {len(apps_data)} apps")
            return apps_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar apps: {e}")
            return []
    
    def get_app_details(self, app_id):
        """Obtém detalhes completos de um aplicativo"""
        try:
            logger.info(f"Obtendo detalhes do app: {app_id}")
            
            # Adicionar delay para evitar rate limiting
            time.sleep(random.uniform(*self.delay_range))
            
            result = app(app_id, lang='pt', country='br')
            app_data = {
                'app_id': app_id,
                'name': result.get('title', ''),
                'store': 'google_play',
                'current_version': result.get('version', ''),
                'rating': result.get('score', 0),
                'total_reviews': result.get('reviews', 0),
                'category': result.get('genre', ''),
                'description': result.get('description', ''),
                'icon_url': result.get('icon', ''),
                'developer': result.get('developer', ''),
                'price': result.get('price', 0),
                'free': result.get('free', True),
                'last_updated': datetime.now(timezone.utc)
            }
            
            logger.info(f"Detalhes obtidos para {app_data['name']}")
            return app_data
            
        except Exception as e:
            logger.error(f"Erro ao obter detalhes do app {app_id}: {e}")
            return None
    
    def get_app_reviews(self, app_id, count=100):
        """Obtém reviews de um aplicativo"""
        try:
            logger.info(f"Coletando {count} reviews do app: {app_id}")
            
            # Adicionar delay para evitar rate limiting
            time.sleep(random.uniform(*self.delay_range))
            
            result, continuation_token = reviews(
                app_id,
                lang='pt',
                country='br',
                sort=Sort.NEWEST,
                count=count
            )
            
            reviews_data = []
            for review in result:
                review_data = {
                    'app_id': app_id,
                    'review_id': review.get('reviewId', ''),
                    'user_name': review.get('userName', 'Usuário Anônimo'),
                    'content': review.get('content', ''),
                    'rating': review.get('score', 0),
                    'date': review.get('at', datetime.now(timezone.utc)),
                    'thumbs_up': review.get('thumbsUpCount', 0),
                    'reply_content': review.get('replyContent', ''),
                    'reply_date': review.get('repliedAt', None)
                }
                reviews_data.append(review_data)
            
            logger.info(f"Coletadas {len(reviews_data)} reviews")
            return reviews_data, continuation_token
            
        except Exception as e:
            logger.error(f"Erro ao coletar reviews do app {app_id}: {e}")
            return [], None
    
    def get_more_reviews(self, app_id, continuation_token, count=100):
        """Obtém mais reviews usando token de continuação"""
        try:
            logger.info(f"Coletando mais {count} reviews do app: {app_id}")
            
            # Adicionar delay para evitar rate limiting
            time.sleep(random.uniform(*self.delay_range))
            
            result, new_token = reviews(
                app_id,
                lang='pt',
                country='br',
                sort=Sort.NEWEST,
                count=count,
                continuation_token=continuation_token
            )
            
            reviews_data = []
            for review in result:
                review_data = {
                    'app_id': app_id,
                    'review_id': review.get('reviewId', ''),
                    'user_name': review.get('userName', 'Usuário Anônimo'),
                    'content': review.get('content', ''),
                    'rating': review.get('score', 0),
                    'date': review.get('at', datetime.now(timezone.utc)),
                    'thumbs_up': review.get('thumbsUpCount', 0),
                    'reply_content': review.get('replyContent', ''),
                    'reply_date': review.get('repliedAt', None)
                }
                reviews_data.append(review_data)
            
            logger.info(f"Coletadas {len(reviews_data)} reviews adicionais")
            return reviews_data, new_token
            
        except Exception as e:
            logger.error(f"Erro ao coletar mais reviews do app {app_id}: {e}")
            return [], None
    
    def get_popular_apps_by_category(self, category='communication', limit=20):
        """Obtém apps populares por categoria"""
        try:
            logger.info(f"Buscando apps populares da categoria: {category}")
            
            # Mapear categorias para termos de busca
            category_terms = {
                'communication': 'whatsapp telegram messenger',
                'social': 'instagram facebook twitter',
                'entertainment': 'netflix youtube spotify',
                'productivity': 'microsoft office google',
                'games': 'games jogos',
                'shopping': 'shopping compras mercado',
                'finance': 'banco financeiro pagamento'
            }
            
            search_term = category_terms.get(category, category)
            return self.search_apps(search_term, limit)
            
        except Exception as e:
            logger.error(f"Erro ao buscar apps da categoria {category}: {e}")
            return []





