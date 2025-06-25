import requests
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import base64

logger = logging.getLogger(__name__)

class JiraIntegrationService:
    """Serviço para integração com Jira API"""
    
    def __init__(self, jira_url: str, email: str, api_token: str):
        """
        Inicializa o serviço Jira
        
        Args:
            jira_url: URL base do Jira (ex: https://company.atlassian.net)
            email: Email do usuário Jira
            api_token: Token de API do Jira
        """
        self.jira_url = jira_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        
        # Criar header de autenticação
        auth_string = f"{email}:{api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testa a conexão com o Jira
        
        Returns:
            Dict com resultado do teste
        """
        try:
            response = requests.get(
                f"{self.jira_url}/rest/api/3/myself",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "success": True,
                    "message": "Conexão com Jira estabelecida com sucesso",
                    "user": user_data.get('displayName', 'Unknown'),
                    "account_id": user_data.get('accountId')
                }
            else:
                return {
                    "success": False,
                    "message": f"Erro na autenticação: {response.status_code}",
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Erro ao testar conexão Jira: {e}")
            return {
                "success": False,
                "message": f"Erro de conexão: {str(e)}"
            }
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Obtém lista de projetos disponíveis
        
        Returns:
            Lista de projetos
        """
        try:
            response = requests.get(
                f"{self.jira_url}/rest/api/3/project",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                projects = response.json()
                return [
                    {
                        "id": project.get('id'),
                        "key": project.get('key'),
                        "name": project.get('name'),
                        "projectTypeKey": project.get('projectTypeKey')
                    }
                    for project in projects
                ]
            else:
                logger.error(f"Erro ao buscar projetos: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Erro ao buscar projetos Jira: {e}")
            return []
    
    def get_issue_types(self, project_key: str) -> List[Dict[str, Any]]:
        """
        Obtém tipos de issue disponíveis para um projeto
        
        Args:
            project_key: Chave do projeto
            
        Returns:
            Lista de tipos de issue
        """
        try:
            response = requests.get(
                f"{self.jira_url}/rest/api/3/project/{project_key}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                project_data = response.json()
                issue_types = project_data.get('issueTypes', [])
                return [
                    {
                        "id": issue_type.get('id'),
                        "name": issue_type.get('name'),
                        "description": issue_type.get('description'),
                        "subtask": issue_type.get('subtask', False)
                    }
                    for issue_type in issue_types
                ]
            else:
                logger.error(f"Erro ao buscar tipos de issue: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Erro ao buscar tipos de issue: {e}")
            return []
    
    def create_issue(self, project_key: str, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria uma nova issue no Jira
        
        Args:
            project_key: Chave do projeto
            issue_data: Dados da issue
            
        Returns:
            Dict com resultado da criação
        """
        try:
            # Mapear prioridade
            priority_map = {
                "High": "High",
                "Medium": "Medium", 
                "Low": "Low"
            }
            
            # Mapear tipo de issue baseado na categoria
            issue_type_map = {
                "Bug": "Bug",
                "Feature": "Story",
                "Improvement": "Story",
                "Performance": "Task",
                "UI/UX": "Story"
            }
            
            category = issue_data.get('category', 'Task')
            issue_type = issue_type_map.get(category, 'Task')
            
            # Preparar dados da issue
            jira_issue = {
                "fields": {
                    "project": {
                        "key": project_key
                    },
                    "summary": issue_data.get('title', 'Issue sem título'),
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": issue_data.get('description', 'Sem descrição')
                                    }
                                ]
                            }
                        ]
                    },
                    "issuetype": {
                        "name": issue_type
                    },
                    "priority": {
                        "name": priority_map.get(issue_data.get('priority', 'Medium'), 'Medium')
                    }
                }
            }
            
            # Adicionar critérios de aceitação se existirem
            acceptance_criteria = issue_data.get('acceptance_criteria', [])
            if acceptance_criteria:
                criteria_text = "\n\nCritérios de Aceitação:\n"
                for i, criteria in enumerate(acceptance_criteria, 1):
                    criteria_text += f"{i}. {criteria}\n"
                
                jira_issue["fields"]["description"]["content"].append({
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": criteria_text
                        }
                    ]
                })
            
            # Adicionar evidências se existirem
            evidence = issue_data.get('evidence', [])
            if evidence:
                evidence_text = "\n\nEvidências dos usuários:\n"
                for i, ev in enumerate(evidence, 1):
                    evidence_text += f"{i}. {ev}\n"
                
                jira_issue["fields"]["description"]["content"].append({
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": evidence_text
                        }
                    ]
                })
            
            # Criar issue
            response = requests.post(
                f"{self.jira_url}/rest/api/3/issue",
                headers=self.headers,
                data=json.dumps(jira_issue),
                timeout=30
            )
            
            if response.status_code == 201:
                created_issue = response.json()
                return {
                    "success": True,
                    "issue_key": created_issue.get('key'),
                    "issue_id": created_issue.get('id'),
                    "url": f"{self.jira_url}/browse/{created_issue.get('key')}",
                    "message": "Issue criada com sucesso"
                }
            else:
                logger.error(f"Erro ao criar issue: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"Erro ao criar issue: {response.status_code}",
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Erro ao criar issue no Jira: {e}")
            return {
                "success": False,
                "message": f"Erro ao criar issue: {str(e)}"
            }
    
    def create_backlog_issues(self, project_key: str, backlog_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria múltiplas issues baseadas no backlog gerado pela IA
        
        Args:
            project_key: Chave do projeto Jira
            backlog_data: Dados do backlog gerado pela IA
            
        Returns:
            Dict com resultado da criação das issues
        """
        backlog_items = backlog_data.get('backlog_items', [])
        app_name = backlog_data.get('summary', {}).get('app_name', 'App')
        
        results = {
            "success": True,
            "created_issues": [],
            "failed_issues": [],
            "summary": {
                "total_items": len(backlog_items),
                "created_count": 0,
                "failed_count": 0,
                "app_name": app_name,
                "project_key": project_key
            }
        }
        
        for item in backlog_items:
            # Adicionar prefixo do app no título
            item_with_prefix = item.copy()
            item_with_prefix['title'] = f"[{app_name}] {item.get('title', 'Sem título')}"
            
            # Criar issue
            result = self.create_issue(project_key, item_with_prefix)
            
            if result.get('success'):
                results['created_issues'].append({
                    "title": item.get('title'),
                    "issue_key": result.get('issue_key'),
                    "url": result.get('url'),
                    "priority": item.get('priority'),
                    "category": item.get('category')
                })
                results['summary']['created_count'] += 1
            else:
                results['failed_issues'].append({
                    "title": item.get('title'),
                    "error": result.get('message'),
                    "item_data": item
                })
                results['summary']['failed_count'] += 1
        
        # Se alguma issue falhou, marcar como parcialmente bem-sucedido
        if results['summary']['failed_count'] > 0:
            results['success'] = results['summary']['created_count'] > 0
        
        return results
    
    def create_epic_for_app(self, project_key: str, app_name: str, backlog_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um épico para agrupar todas as issues do app
        
        Args:
            project_key: Chave do projeto
            app_name: Nome do aplicativo
            backlog_summary: Resumo do backlog
            
        Returns:
            Dict com resultado da criação do épico
        """
        try:
            epic_data = {
                "fields": {
                    "project": {
                        "key": project_key
                    },
                    "summary": f"Melhorias para {app_name} - Análise de Reviews",
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Épico criado automaticamente baseado na análise de {backlog_summary.get('total_reviews_analyzed', 0)} reviews do aplicativo {app_name}.\n\n"
                                                f"Problemas críticos identificados: {backlog_summary.get('critical_issues_found', 0)}\n"
                                                f"Sugestões de melhoria: {backlog_summary.get('improvement_suggestions', 0)}\n\n"
                                                f"Este épico agrupa todas as tarefas geradas pela análise de IA dos comentários dos usuários."
                                    }
                                ]
                            }
                        ]
                    },
                    "issuetype": {
                        "name": "Epic"
                    }
                }
            }
            
            response = requests.post(
                f"{self.jira_url}/rest/api/3/issue",
                headers=self.headers,
                data=json.dumps(epic_data),
                timeout=30
            )
            
            if response.status_code == 201:
                created_epic = response.json()
                return {
                    "success": True,
                    "epic_key": created_epic.get('key'),
                    "epic_id": created_epic.get('id'),
                    "url": f"{self.jira_url}/browse/{created_epic.get('key')}",
                    "message": "Épico criado com sucesso"
                }
            else:
                logger.error(f"Erro ao criar épico: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"Erro ao criar épico: {response.status_code}",
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Erro ao criar épico no Jira: {e}")
            return {
                "success": False,
                "message": f"Erro ao criar épico: {str(e)}"
            }

