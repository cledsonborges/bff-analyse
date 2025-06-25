
import logging
import random
from typing import List, Dict

logger = logging.getLogger(__name__)

class BacklogGenerationFallbackService:
    def __init__(self):
        logger.info("Serviço de fallback de geração de backlog inicializado.")

    def generate_mock_backlog(self, app_name: str, reviews: List[Dict]) -> Dict:
        """
        Gera um backlog de exemplo baseado nas reviews fornecidas.
        Este é um fallback quando a IA real não está disponível.
        """
        logger.info(f"Gerando backlog de exemplo para o app: {app_name}")

        total_reviews = len(reviews)
        if total_reviews == 0:
            return {
                "app_name": app_name,
                "total_reviews_processed": 0,
                "generated_backlog_items": [],
                "summary": "Nenhuma review disponível para gerar backlog."
            }

        # Simular alguns itens de backlog baseados em palavras-chave ou categorias gerais
        possible_issues = [
            "Melhorar desempenho do aplicativo",
            "Corrigir bugs de travamento",
            "Adicionar novas funcionalidades",
            "Melhorar interface do usuário",
            "Otimizar consumo de bateria",
            "Aprimorar suporte ao cliente",
            "Atualizar conteúdo",
            "Resolver problemas de login",
            "Melhorar estabilidade da conexão"
        ]

        possible_improvements = [
            "Adicionar modo escuro",
            "Integrar com outras plataformas",
            "Personalização de temas",
            "Novos recursos de compartilhamento",
            "Melhorar notificações",
            "Otimizar para tablets",
            "Adicionar tutoriais interativos"
        ]

        num_issues = random.randint(1, min(3, len(possible_issues)))
        num_improvements = random.randint(1, min(2, len(possible_improvements)))

        generated_items = []
        for _ in range(num_issues):
            item = {
                "type": "issue",
                "priority": random.choice(["High", "Medium", "Low"]),
                "description": random.choice(possible_issues),
                "source": "Fallback AI (simulado)"
            }
            if item["description"] not in [i["description"] for i in generated_items]:
                generated_items.append(item)

        for _ in range(num_improvements):
            item = {
                "type": "improvement",
                "priority": random.choice(["Medium", "Low"]),
                "description": random.choice(possible_improvements),
                "source": "Fallback AI (simulado)"
            }
            if item["description"] not in [i["description"] for i in generated_items]:
                generated_items.append(item)

        # Adicionar um item de backlog genérico baseado no sentimento geral
        positive_reviews = [r for r in reviews if r.get('sentiment', '') == 'positive']
        negative_reviews = [r for r in reviews if r.get('sentiment', '') == 'negative']

        if len(positive_reviews) > len(negative_reviews) * 2:
            generated_items.append({
                "type": "feedback",
                "priority": "Low",
                "description": "Manter a qualidade atual e coletar mais feedback positivo.",
                "source": "Fallback AI (simulado)"
            })
        elif len(negative_reviews) > len(positive_reviews) * 2:
            generated_items.append({
                "type": "critical_feedback",
                "priority": "High",
                "description": "Investigar as principais reclamações dos usuários para evitar churn.",
                "source": "Fallback AI (simulado)"
            })
        else:
            generated_items.append({
                "type": "general_feedback",
                "priority": "Medium",
                "description": "Analisar feedback misto para identificar áreas de melhoria e pontos fortes.",
                "source": "Fallback AI (simulado)"
            })

        summary_message = f"Backlog gerado com {len(generated_items)} itens a partir de {total_reviews} reviews."

        return {
            "app_name": app_name,
            "total_reviews_processed": total_reviews,
            "generated_backlog_items": generated_items,
            "summary": summary_message
        }


