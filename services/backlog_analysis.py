import google.generativeai as genai
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class BacklogAnalysisService:
    """Serviço para análise de reviews e geração de backlog com IA usando Gemini"""
    
    def __init__(self, api_key: str):
        """
        Inicializa o serviço com a API key do Gemini
        
        Args:
            api_key: Chave da API do Google Gemini
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def analyze_reviews_for_backlog(self, reviews: List[Dict], app_name: str) -> Dict[str, Any]:
        """
        Analisa reviews para identificar problemas e gerar itens de backlog
        
        Args:
            reviews: Lista de reviews do aplicativo
            app_name: Nome do aplicativo
            
        Returns:
            Dict contendo análise e itens de backlog gerados
        """
        try:
            # Preparar texto dos reviews para análise
            reviews_text = self._prepare_reviews_text(reviews)
            
            # Prompt para análise de problemas e geração de backlog
            prompt = f"""
            Analise os seguintes reviews do aplicativo "{app_name}" e identifique problemas técnicos, bugs, crashes, falhas de usabilidade e melhorias sugeridas pelos usuários.

            Reviews:
            {reviews_text}

            Com base na análise, gere um backlog de desenvolvimento estruturado em JSON válido com o seguinte formato EXATO:

            {{
                "summary": {{
                    "total_reviews_analyzed": {len(reviews)},
                    "critical_issues_found": 0,
                    "improvement_suggestions": 0,
                    "app_name": "{app_name}"
                }},
                "backlog_items": [
                    {{
                        "title": "Título da tarefa",
                        "description": "Descrição detalhada do problema ou melhoria",
                        "priority": "High",
                        "category": "Bug",
                        "estimated_effort": "5",
                        "user_impact": "High",
                        "evidence": ["review que menciona o problema"],
                        "acceptance_criteria": ["critério 1", "critério 2"]
                    }}
                ]
            }}

            INSTRUÇÕES IMPORTANTES:
            1. Retorne APENAS o JSON válido, sem texto adicional antes ou depois
            2. Use aspas duplas para todas as strings
            3. Não use quebras de linha dentro das strings
            4. Prioridades: "High", "Medium", "Low"
            5. Categorias: "Bug", "Feature", "Improvement", "Performance", "UI/UX"
            6. Esforço estimado: "1", "2", "3", "5", "8", "13"
            7. Impacto no usuário: "High", "Medium", "Low"
            8. Atualize os contadores no summary baseado nos itens gerados

            Foque em:
            - Crashes e falhas técnicas (prioridade alta)
            - Problemas de performance (prioridade alta/média)
            - Bugs de funcionalidade (prioridade média/alta)
            - Melhorias de UX/UI (prioridade média/baixa)
            - Novas funcionalidades solicitadas (prioridade baixa/média)
            """
            
            response = self.model.generate_content(prompt)
            
            # Limpar e extrair JSON da resposta
            response_text = response.text.strip()
            
            # Remover possíveis marcadores de código
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse da resposta JSON
            try:
                backlog_data = json.loads(response_text)
                
                # Validar estrutura básica
                if not isinstance(backlog_data, dict) or 'summary' not in backlog_data or 'backlog_items' not in backlog_data:
                    raise ValueError("Estrutura JSON inválida")
                
                # Adicionar metadados
                backlog_data["metadata"] = {
                    "generated_at": datetime.now().isoformat(),
                    "generated_by": "Gemini AI",
                    "app_name": app_name,
                    "reviews_count": len(reviews)
                }
                
                return backlog_data
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Erro ao fazer parse do JSON da resposta do Gemini: {e}")
                logger.error(f"Resposta recebida: {response_text}")
                
                # Fallback: retornar estrutura básica
                return self._create_fallback_backlog(reviews, app_name, response_text)
                
        except Exception as e:
            logger.error(f"Erro na análise de backlog: {e}")
            return self._create_error_response(str(e), app_name)
    
    def _prepare_reviews_text(self, reviews: List[Dict]) -> str:
        """
        Prepara o texto dos reviews para análise
        
        Args:
            reviews: Lista de reviews
            
        Returns:
            String formatada com os reviews
        """
        reviews_text = ""
        for i, review in enumerate(reviews[:50]):  # Limitar a 50 reviews para não exceder limite de tokens
            rating = review.get('rating', 'N/A')
            content = review.get('content', review.get('text', ''))
            
            if content:
                reviews_text += f"Review {i+1} (Rating: {rating}): {content}\n\n"
        
        return reviews_text
    
    def _create_fallback_backlog(self, reviews: List[Dict], app_name: str, ai_response: str) -> Dict[str, Any]:
        """
        Cria um backlog básico quando há erro no parse do JSON
        
        Args:
            reviews: Lista de reviews
            app_name: Nome do aplicativo
            ai_response: Resposta original da IA
            
        Returns:
            Dict com backlog básico
        """
        # Tentar extrair JSON parcial da resposta
        try:
            # Procurar por JSON válido na resposta
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                potential_json = json_match.group(0)
                try:
                    parsed_data = json.loads(potential_json)
                    if isinstance(parsed_data, dict) and 'backlog_items' in parsed_data:
                        # JSON parcial válido encontrado
                        if 'summary' not in parsed_data:
                            parsed_data['summary'] = {
                                "total_reviews_analyzed": len(reviews),
                                "critical_issues_found": len([item for item in parsed_data.get('backlog_items', []) if item.get('priority') == 'High']),
                                "improvement_suggestions": len([item for item in parsed_data.get('backlog_items', []) if item.get('category') in ['Improvement', 'Feature']]),
                                "app_name": app_name
                            }
                        
                        parsed_data["metadata"] = {
                            "generated_at": datetime.now().isoformat(),
                            "generated_by": "Gemini AI (Partial Parse)",
                            "app_name": app_name,
                            "reviews_count": len(reviews)
                        }
                        
                        return parsed_data
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass
        
        # Se não conseguir extrair JSON válido, criar estrutura básica
        return {
            "summary": {
                "total_reviews_analyzed": len(reviews),
                "critical_issues_found": 0,
                "improvement_suggestions": 0,
                "app_name": app_name,
                "error": "Erro no parse da resposta da IA"
            },
            "backlog_items": [
                {
                    "title": "Análise manual necessária",
                    "description": f"A IA gerou uma resposta que precisa ser analisada manualmente. Resposta: {ai_response[:500]}{'...' if len(ai_response) > 500 else ''}",
                    "priority": "Medium",
                    "category": "Analysis",
                    "estimated_effort": "3",
                    "user_impact": "Medium",
                    "evidence": ["Resposta da IA não estruturada"],
                    "acceptance_criteria": ["Revisar resposta da IA", "Extrair itens manualmente", "Criar tarefas específicas"]
                }
            ],
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generated_by": "Fallback System",
                "app_name": app_name,
                "reviews_count": len(reviews),
                "original_ai_response": ai_response
            }
        }
    
    def _create_error_response(self, error_message: str, app_name: str) -> Dict[str, Any]:
        """
        Cria resposta de erro
        
        Args:
            error_message: Mensagem de erro
            app_name: Nome do aplicativo
            
        Returns:
            Dict com informações de erro
        """
        return {
            "summary": {
                "total_reviews_analyzed": 0,
                "critical_issues_found": 0,
                "improvement_suggestions": 0,
                "app_name": app_name,
                "error": error_message
            },
            "backlog_items": [],
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generated_by": "Error Handler",
                "app_name": app_name,
                "reviews_count": 0,
                "error": error_message
            }
        }
    
    def categorize_issues(self, backlog_items: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categoriza os itens do backlog por tipo
        
        Args:
            backlog_items: Lista de itens do backlog
            
        Returns:
            Dict com itens categorizados
        """
        categories = {
            "critical_bugs": [],
            "performance_issues": [],
            "ui_ux_improvements": [],
            "feature_requests": [],
            "other": []
        }
        
        for item in backlog_items:
            category = item.get('category', '').lower()
            priority = item.get('priority', '').lower()
            
            if category == 'bug' and priority == 'high':
                categories["critical_bugs"].append(item)
            elif category == 'performance':
                categories["performance_issues"].append(item)
            elif category in ['ui/ux', 'improvement']:
                categories["ui_ux_improvements"].append(item)
            elif category == 'feature':
                categories["feature_requests"].append(item)
            else:
                categories["other"].append(item)
        
        return categories
    
    def generate_sprint_recommendations(self, backlog_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera recomendações de sprint baseadas no backlog
        
        Args:
            backlog_data: Dados do backlog gerado
            
        Returns:
            Dict com recomendações de sprint
        """
        backlog_items = backlog_data.get('backlog_items', [])
        categorized = self.categorize_issues(backlog_items)
        
        # Calcular esforço total por categoria
        effort_by_category = {}
        for category, items in categorized.items():
            total_effort = sum(int(item.get('estimated_effort', 3)) for item in items)
            effort_by_category[category] = {
                "total_effort": total_effort,
                "item_count": len(items),
                "items": items
            }
        
        # Gerar recomendações
        recommendations = {
            "sprint_1": {
                "focus": "Correção de bugs críticos",
                "items": categorized["critical_bugs"][:5],  # Máximo 5 itens críticos
                "estimated_effort": sum(int(item.get('estimated_effort', 3)) for item in categorized["critical_bugs"][:5])
            },
            "sprint_2": {
                "focus": "Melhorias de performance",
                "items": categorized["performance_issues"][:3],
                "estimated_effort": sum(int(item.get('estimated_effort', 3)) for item in categorized["performance_issues"][:3])
            },
            "sprint_3": {
                "focus": "Melhorias de UX/UI",
                "items": categorized["ui_ux_improvements"][:4],
                "estimated_effort": sum(int(item.get('estimated_effort', 3)) for item in categorized["ui_ux_improvements"][:4])
            }
        }
        
        return {
            "recommendations": recommendations,
            "summary": effort_by_category,
            "total_items": len(backlog_items),
            "generated_at": datetime.now().isoformat()
        }

