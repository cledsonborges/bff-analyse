## Agente de IA para Análise de Aplicativos - Back-end

Este é o back-end do sistema de análise automática de aplicativos da Google Play Store e Apple App Store.
#
## Funcionalidades

- 🔍 **Scraping de Dados**: Coleta automática de avaliações e informações dos apps
- 🤖 **Análise de Sentimentos**: Classificação inteligente usando Google Gemini (com fallback)
- 📊 **Dashboards**: APIs para visualização de dados e métricas
- 📝 **Geração de Backlog**: Geração de itens de backlog baseados em reviews (com fallback)

## APIs Disponíveis

### Apps
- `GET /api/apps` - Lista todos os aplicativos
- `GET /api/apps/{id}` - Detalhes de um aplicativo específico
- `GET /api/apps/{id}/reviews` - Reviews de um aplicativo

### Análise
- `GET /api/apps/{id}/analysis` - Análise de sentimentos de um aplicativo
- `GET /api/apps/{id}/backlog` - Geração de itens de backlog para um aplicativo

### Utilitários
- `GET /health` - Status da API

## Tecnologias

- **Flask**: Framework web Python
- **Google Gemini**: IA para análise de sentimentos
- **Google Play Scraper**: Coleta de dados do Google Play
- **App Store Scraper**: Coleta de dados da Apple Store

## Deploy

Este projeto está configurado para deploy automático na Vercel.

## Configuração

Para funcionalidades completas, configure as seguintes variáveis de ambiente:

- `GEMINI_API_KEY`: Chave da API do Google Gemini

## Desenvolvido por

Cledson Alves - Sistema completo de análise automática de aplicativos.


