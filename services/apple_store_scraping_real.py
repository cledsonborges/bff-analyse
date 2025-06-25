import logging
import requests
import time
import random
from datetime import datetime, timezone

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
            response = requests.get(search_url, params=params, timeout=30)
            
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
            response = requests.get(lookup_url, params=params, timeout=30)
            
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
                'last_updated': datetime.now(timezone.utc)
            }
            
            logger.info(f"Detalhes obtidos para {app_data['name']}")
            return app_data
            
        except Exception as e:
            logger.error(f"Erro ao obter detalhes do app {app_id}: {e}")
            return None
    
    def get_app_reviews(self, app_id, count=100):
        """Obtém reviews de um aplicativo usando RSS feed (método alternativo)"""
        try:
            logger.info(f"Tentando coletar reviews do app: {app_id}")
            
            time.sleep(random.uniform(*self.delay_range))
            
            # Usar RSS feed para reviews (método limitado mas funcional)
            rss_url = f"{self.base_url}/br/rss/customerreviews/id={app_id}/json"
            
            response = requests.get(rss_url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"Não foi possível obter reviews via RSS para app {app_id}")
                return []
            
            data = response.json()
            entries = data.get('feed', {}).get('entry', [])
            
            # Pular a primeira entrada que é metadados do app
            review_entries = entries[1:] if len(entries) > 1 else []
            
            reviews_data = []
            for i, entry in enumerate(review_entries[:count]):
                try:
                    # Processar entry do RSS
                    content = entry.get('content', {}).get('label', '')
                    author = entry.get('author', {}).get('name', {}).get('label', 'Usuário Anônimo')
                    rating_text = entry.get('im:rating', {}).get('label', '0')
                    
                    # Extrair rating numérico
                    try:
                        rating = int(rating_text)
                    except:
                        rating = 0
                    
                    review_data = {
                        'app_id': app_id,
                        'review_id': f"{app_id}_{i}",
                        'user_name': author,
                        'content': content,
                        'rating': rating,
                        'date': datetime.now(timezone.utc),
                        'title': entry.get('title', {}).get('label', ''),
                        'version': entry.get('im:version', {}).get('label', '')
                    }
                    reviews_data.append(review_data)
                except Exception as review_error:
                    logger.warning(f"Erro ao processar review individual: {review_error}")
                    continue
            
            logger.info(f"Coletadas {len(reviews_data)} reviews via RSS")
            return reviews_data
            
        except Exception as e:
            logger.error(f"Erro ao coletar reviews do app {app_id}: {e}")
            # Retornar lista vazia em caso de erro, mas não falhar completamente
            logger.info(f"Retornando lista vazia de reviews para app {app_id}")
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
            response = requests.get(charts_url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Erro ao obter charts: {response.status_code}")
                return []
            
            data = response.json()
            entries = data.get('feed', {}).get('entry', [])
            
            apps_data = []
            for entry in entries:
                try:
                    # Extrair ID do app da URL
                    app_url = entry.get('id', {}).get('attributes', {}).get('im:id', '')
                    
                    # Pegar informações das imagens (diferentes tamanhos disponíveis)
                    images = entry.get('im:image', [])
                    icon_url = images[-1].get('label', '') if images else ''
                    
                    # Processar preço
                    price_info = entry.get('im:price', {}).get('attributes', {})
                    price = price_info.get('amount', '0')
                    try:
                        price = float(price)
                    except:
                        price = 0
                    
                    app_data = {
                        'app_id': app_url,
                        'name': entry.get('im:name', {}).get('label', ''),
                        'store': 'app_store',
                        'category': entry.get('category', {}).get('attributes', {}).get('label', ''),
                        'icon_url': icon_url,
                        'developer': entry.get('im:artist', {}).get('label', ''),
                        'price': price,
                        'free': price == 0
                    }
                    apps_data.append(app_data)
                except Exception as app_error:
                    logger.warning(f"Erro ao processar app individual dos charts: {app_error}")
                    continue
            
            logger.info(f"Obtidos {len(apps_data)} apps dos charts")
            return apps_data
            
        except Exception as e:
            logger.error(f"Erro ao obter top charts: {e}")
            return []

    def get_app_reviews_alternative(self, app_id, count=100):
        """Método alternativo para obter reviews (placeholder para futuras implementações)"""
        logger.info(f"Método alternativo de reviews não implementado para app {app_id}")
        logger.info("Retornando informações básicas do app como fallback")
        
        # Como fallback, retorna detalhes básicos do app formatados como "review"
        app_details = self.get_app_details(app_id)
        if app_details:
            fallback_review = {
                'app_id': app_id,
                'review_id': f"{app_id}_fallback",
                'user_name': 'Sistema',
                'content': f"App: {app_details.get('name', 'N/A')} - {app_details.get('description', 'Sem descrição')[:200]}...",
                'rating': app_details.get('rating', 0),
                'date': datetime.now(timezone.utc),
                'title': 'Informações do App',
                'version': app_details.get('current_version', '')
            }
            return [fallback_review]
        
        return []