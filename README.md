## Agente de IA para Análise de Aplicativos - Back-end

Este é o back-end do sistema de análise automática de aplicativos da Google Play Store e Apple App Store.

## Funcionalidades

- 🔍 **Scraping de Dados**: Coleta automática de avaliações e informações dos apps
- 🤖 **Análise de Sentimentos**: Classificação inteligente usando Google Gemini
- 📊 **Dashboards**: APIs para visualização de dados e métricas
- 🚨 **Automação**: Criação automática de issues no GitHub baseada em tendências negativas
- 🔄 **Comparação**: Análise comparativa com aplicativos concorrentes

## APIs Disponíveis

### Apps
- `GET /api/apps` - Lista todos os aplicativos
- `GET /api/apps/{id}` - Detalhes de um aplicativo específico
- `GET /api/apps/{id}/reviews` - Reviews de um aplicativo

### Scraping
- `POST /api/scraping/google-play/{id}` - Fazer scraping do Google Play
- `POST /api/scraping/apple-store/{id}` - Fazer scraping da Apple Store

### Análise de Sentimentos
- `POST /api/sentiment/analyze` - Analisar sentimentos das reviews

### Automação GitHub
- `GET /api/github/config` - Configuração do GitHub
- `POST /api/github/simulate-issue/{id}` - Simular criação de issue

### Utilitários
- `GET /health` - Status da API

## Tecnologias

- **Flask**: Framework web Python
- **Google Gemini**: IA para análise de sentimentos
- **PyGithub**: Automação de issues
- **Google Play Scraper**: Coleta de dados do Google Play
- **App Store Scraper**: Coleta de dados da Apple Store

## Deploy

Este projeto está configurado para deploy automático na Vercel.

## Configuração

Para funcionalidades completas, configure as seguintes variáveis de ambiente:

- `GEMINI_API_KEY`: Chave da API do Google Gemini
- `GITHUB_TOKEN`: Token de acesso do GitHub
- `GITHUB_REPO`: Repositório para criação de issues (formato: owner/repo)

## Desenvolvido por

Cledson Alves - Sistema completo de análise automática de aplicativos.

