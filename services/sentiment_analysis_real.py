import logging
import google.generativeai as genai
import os
import json
import time
import random
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SentimentAnalysisService:
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o serviço de análise de sentimentos
        
        Args:
            api_key: Chave da API do Gemini. Se não fornecida, tentará obter da variável de ambiente
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY não configurada. Usando análise mock.")
            self.use_mock = True
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                self.use_mock = False
                logger.info("Serviço Gemini configurado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao configurar Gemini: {e}")
                self.use_mock = True
        
        self.delay_range = (1, 2)  # Delay entre requests para evitar rate limiting
    
    def analyze_single_review(self, review_text: str) -> Dict:
        """
        Analisa o sentimento de uma única review
        
        Args:
            review_text: Texto da review para análise
            
        Returns:
            Dict com sentiment ('positive', 'negative', 'neutral') e score (0-1)
        """
        if self.use_mock:
            return self._mock_sentiment_analysis(review_text)
        
        try:
            # Adicionar delay para evitar rate limiting
            time.sleep(random.uniform(*self.delay_range))
            
            prompt = f"""
            Analise o sentimento da seguinte avaliação de aplicativo móvel em português brasileiro.
            
            Avaliação: "{review_text}"
            
            Responda APENAS com um JSON no seguinte formato:
            {{
                "sentiment": "positive|negative|neutral",
                "score": 0.85,
                "reasoning": "breve explicação"
            }}
            
            Critérios:
            - positive: Avaliação claramente positiva, elogios, satisfação
            - negative: Avaliação claramente negativa, críticas, problemas
            - neutral: Avaliação neutra, mista ou sem sentimento claro
            - score: Confiança da análise (0.0 a 1.0)
            """
            
            response = self.model.generate_content(prompt)
            
            # Tentar extrair JSON da resposta
            response_text = response.text.strip()
            
            # Remover markdown se presente
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            result = json.loads(response_text)
            
            # Validar resultado
            if 'sentiment' not in result or 'score' not in result:
                raise ValueError("Resposta inválida do modelo")
            
            if result['sentiment'] not in ['positive', 'negative', 'neutral']:
                raise ValueError("Sentimento inválido")
            
            if not 0 <= result['score'] <= 1:
                raise ValueError("Score inválido")
            
            logger.debug(f"Análise concluída: {result['sentiment']} ({result['score']})")
            return result
            
        except Exception as e:
            logger.error(f"Erro na análise de sentimento: {e}")
            # Fallback para análise mock
            return self._mock_sentiment_analysis(review_text)
    
    def analyze_batch_reviews(self, reviews: List[Dict]) -> List[Dict]:
        """
        Analisa o sentimento de múltiplas reviews
        
        Args:
            reviews: Lista de dicts com 'id' e 'content'
            
        Returns:
            Lista de dicts com resultados da análise
        """
        results = []
        
        for i, review in enumerate(reviews):
            try:
                logger.info(f"Analisando review {i+1}/{len(reviews)}")
                
                analysis = self.analyze_single_review(review['content'])
                
                result = {
                    'review_id': review.get('id'),
                    'sentiment': analysis['sentiment'],
                    'sentiment_score': analysis['score'],
                    'reasoning': analysis.get('reasoning', '')
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Erro ao analisar review {review.get('id', 'unknown')}: {e}")
                # Adicionar resultado mock em caso de erro
                results.append({
                    'review_id': review.get('id'),
                    'sentiment': 'neutral',
                    'sentiment_score': 0.5,
                    'reasoning': 'Erro na análise'
                })
        
        return results
    
    def analyze_app_sentiment_summary(self, app_name: str, reviews_summary: List[Dict]) -> Dict:
        """
        Gera um resumo de sentimentos para um aplicativo
        
        Args:
            app_name: Nome do aplicativo
            reviews_summary: Lista com resumo das reviews analisadas
            
        Returns:
            Dict com resumo da análise
        """
        if self.use_mock:
            return self._mock_app_summary(app_name, reviews_summary)
        
        try:
            # Preparar dados para análise
            positive_count = len([r for r in reviews_summary if r['sentiment'] == 'positive'])
            negative_count = len([r for r in reviews_summary if r['sentiment'] == 'negative'])
            neutral_count = len([r for r in reviews_summary if r['sentiment'] == 'neutral'])
            total_count = len(reviews_summary)
            
            # Selecionar algumas reviews representativas
            sample_reviews = []
            for sentiment in ['positive', 'negative', 'neutral']:
                sentiment_reviews = [r for r in reviews_summary if r['sentiment'] == sentiment]
                if sentiment_reviews:
                    sample_reviews.extend(sentiment_reviews[:2])  # 2 de cada tipo
            
            sample_text = "\n".join([f"- {r.get('content', '')[:100]}..." for r in sample_reviews])
            
            prompt = f"""
            Analise o sentimento geral do aplicativo "{app_name}" baseado nas seguintes estatísticas e amostras de avaliações:
            
            Estatísticas:
            - Total de avaliações: {total_count}
            - Positivas: {positive_count} ({positive_count/total_count*100:.1f}%)
            - Negativas: {negative_count} ({negative_count/total_count*100:.1f}%)
            - Neutras: {neutral_count} ({neutral_count/total_count*100:.1f}%)
            
            Amostras de avaliações:
            {sample_text}
            
            Responda APENAS com um JSON no seguinte formato:
            {{
                "overall_sentiment": "positive|negative|neutral",
                "confidence": 0.85,
                "main_issues": ["problema1", "problema2"],
                "main_positives": ["ponto_positivo1", "ponto_positivo2"],
                "recommendation": "breve recomendação"
            }}
            """
            
            time.sleep(random.uniform(*self.delay_range))
            response = self.model.generate_content(prompt)
            
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            result = json.loads(response_text)
            
            # Adicionar estatísticas calculadas
            result.update({
                'total_reviews': total_count,
                'positive_percentage': round(positive_count/total_count*100, 1) if total_count > 0 else 0,
                'negative_percentage': round(negative_count/total_count*100, 1) if total_count > 0 else 0,
                'neutral_percentage': round(neutral_count/total_count*100, 1) if total_count > 0 else 0
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na análise de resumo: {e}")
            return self._mock_app_summary(app_name, reviews_summary)
    
    def _mock_sentiment_analysis(self, review_text: str) -> Dict:
        """Análise mock para quando a API não está disponível"""
        # Análise simples baseada em palavras-chave
        positive_words = ['bom', 'ótimo', 'excelente', 'perfeito', 'recomendo', 'gosto', 'funciona', 'rápido']
        negative_words = ['ruim', 'péssimo', 'horrível', 'lento', 'trava', 'bug', 'problema', 'não funciona']
        
        text_lower = review_text.lower()
        
        positive_score = sum(1 for word in positive_words if word in text_lower)
        negative_score = sum(1 for word in negative_words if word in text_lower)
        
        if positive_score > negative_score:
            sentiment = 'positive'
            score = min(0.7 + positive_score * 0.1, 0.95)
        elif negative_score > positive_score:
            sentiment = 'negative'
            score = min(0.7 + negative_score * 0.1, 0.95)
        else:
            sentiment = 'neutral'
            score = 0.6
        
        return {
            'sentiment': sentiment,
            'score': score,
            'reasoning': 'Análise baseada em palavras-chave (mock)'
        }
    
    def _mock_app_summary(self, app_name: str, reviews_summary: List[Dict]) -> Dict:
        """Resumo mock para quando a API não está disponível"""
        positive_count = len([r for r in reviews_summary if r['sentiment'] == 'positive'])
        negative_count = len([r for r in reviews_summary if r['sentiment'] == 'negative'])
        neutral_count = len([r for r in reviews_summary if r['sentiment'] == 'neutral'])
        total_count = len(reviews_summary)
        
        if positive_count > negative_count:
            overall_sentiment = 'positive'
        elif negative_count > positive_count:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        return {
            'overall_sentiment': overall_sentiment,
            'confidence': 0.7,
            'main_issues': ['Análise mock ativa'],
            'main_positives': ['Configure GEMINI_API_KEY para análise real'],
            'recommendation': 'Configure a API do Gemini para análises mais precisas',
            'total_reviews': total_count,
            'positive_percentage': round(positive_count/total_count*100, 1) if total_count > 0 else 0,
            'negative_percentage': round(negative_count/total_count*100, 1) if total_count > 0 else 0,
            'neutral_percentage': round(neutral_count/total_count*100, 1) if total_count > 0 else 0
        }

