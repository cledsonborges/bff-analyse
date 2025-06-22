import logging
from app_store_scraper import AppStore
import requests
import time
import random
from datetime import datetime

logger = logging.getLogger(__name__)

class AppleAppStoreScrapingService:
    def __init__(self):
        self.delay_range = (1, 3)  # Delay entre requests para evitar rate limiting
        self.base_url = "https://itunes.apple.com"
    
    def search_apps(self, query, limit=10):
        """Busca aplicativos na Apple App Store"""
        try:
            logger.info(f"Buscando apps na App Store: {query}")
            
            # Usar API de busca do iTunes
            search_url = f"{self.base_url}/search"
            params = {
                'term': query,
                'country': 'br',
                'media': 'software',
                'limit': limit
            }
            
            time.sleep(random.uniform(*self.delay_range))
            response = requests.get(search_url, params=params)
            
            if response.status_code != 200:
                logger.error(f"Erro na busca: {response.status_code}")
                return []
            
            data = response.json()
            apps_data = []
            
            for result in data.get('results', []):
                app_data = {
                    'app_id': str(result.get('trackId', '')),
                    'name': result.get('trackName', ''),
                    'store': 'app_store',
                    'category': result.get('primaryGenreName', ''),
                    'rating': result.get('averageUserRating', 0),
                    'total_reviews': result.get('userRatingCount', 0),
                    'icon_url': result.get('artworkUrl512', ''),
                    'description': result.get('description', ''),
                    'developer': result.get('artistName', ''),
                    'price': result.get('price', 0),
                    'current_version': result.get('version', '')
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
            
            # Usar API do iTunes para detalhes
            lookup_url = f"{self.base_url}/lookup"
            params = {
                'id': app_id,
                'country': 'br'
            }
            
            time.sleep(random.uniform(*self.delay_range))
            response = requests.get(lookup_url, params=params)
            
            if response.status_code != 200:
                logger.error(f"Erro ao obter detalhes: {response.status_code}")
                return None
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                logger.warning(f"App {app_id} não encontrado")
                return None
            
            result = results[0]
            app_data = {
                'app_id': str(result.get('trackId', '')),
                'name': result.get('trackName', ''),
                'store': 'app_store',
                'current_version': result.get('version', ''),
                'rating': result.get('averageUserRating', 0),
                'total_reviews': result.get('userRatingCount', 0),
                'category': result.get('primaryGenreName', ''),
                'description': result.get('description', ''),
                'icon_url': result.get('artworkUrl512', ''),
                'developer': result.get('artistName', ''),
                'price': result.get('price', 0),
                'free': result.get('price', 0) == 0,
                'last_updated': datetime.utcnow()
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
            
            time.sleep(random.uniform(*self.delay_range))
            
            # Usar app-store-scraper para reviews
            app_store = AppStore(country='br', app_name='', app_id=app_id)
            app_store.review(how_many=count)
            
            reviews_data = []
            for review in app_store.reviews:
                review_data = {
                    'app_id': app_id,
                    'review_id': review.get('id', ''),
                    'user_name': review.get('userName', 'Usuário Anônimo'),
                    'content': review.get('review', ''),
                    'rating': review.get('rating', 0),
                    'date': review.get('date', datetime.utcnow()),
                    'title': review.get('title', ''),
                    'version': review.get('version', '')
                }
                reviews_data.append(review_data)
            
            logger.info(f"Coletadas {len(reviews_data)} reviews")
            return reviews_data
            
        except Exception as e:
            logger.error(f"Erro ao coletar reviews do app {app_id}: {e}")
            return []
    
    def get_popular_apps_by_category(self, category='social-networking', limit=20):
        """Obtém apps populares por categoria"""
        try:
            logger.info(f"Buscando apps populares da categoria: {category}")
            
            # Mapear categorias para termos de busca
            category_terms = {
                'social-networking': 'whatsapp instagram facebook',
                'entertainment': 'netflix youtube spotify',
                'productivity': 'microsoft office google',
                'games': 'games',
                'shopping': 'shopping',
                'finance': 'bank banking finance',
                'photo-video': 'camera photo video',
                'music': 'music spotify'
            }
            
            search_term = category_terms.get(category, category)
            return self.search_apps(search_term, limit)
            
        except Exception as e:
            logger.error(f"Erro ao buscar apps da categoria {category}: {e}")
            return []
    
    def get_top_charts(self, genre_id=6005, limit=50):
        """Obtém top charts da App Store"""
        try:
            logger.info(f"Obtendo top charts do gênero: {genre_id}")
            
            # URL para top charts
            charts_url = f"{self.base_url}/br/rss/topfreeapplications/limit={limit}/genre={genre_id}/json"
            
            time.sleep(random.uniform(*self.delay_range))
            response = requests.get(charts_url)
            
            if response.status_code != 200:
                logger.error(f"Erro ao obter charts: {response.status_code}")
                return []
            
            data = response.json()
            entries = data.get('feed', {}).get('entry', [])
            
            apps_data = []
            for entry in entries:
                # Extrair ID do app da URL
                app_url = entry.get('id', {}).get('attributes', {}).get('im:id', '')
                
                app_data = {
                    'app_id': app_url,
                    'name': entry.get('im:name', {}).get('label', ''),
                    'store': 'app_store',
                    'category': entry.get('category', {}).get('attributes', {}).get('label', ''),
                    'icon_url': entry.get('im:image', [{}])[-1].get('label', ''),
                    'developer': entry.get('im:artist', {}).get('label', ''),
                    'price': entry.get('im:price', {}).get('attributes', {}).get('amount', '0')
                }
                apps_data.append(app_data)
            
            logger.info(f"Obtidos {len(apps_data)} apps dos charts")
            return apps_data
            
        except Exception as e:
            logger.error(f"Erro ao obter top charts: {e}")
            return []

