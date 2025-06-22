from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Dados mock para demonstração
mock_apps = [
    {
        "app_id": "com.whatsapp",
        "name": "WhatsApp Messenger",
        "store": "google_play",
        "current_version": "2.23.25.84",
        "rating": 4.1,
        "total_reviews": 50000000,
        "category": "Comunicação"
    },
    {
        "app_id": "310633997",
        "name": "WhatsApp Messenger",
        "store": "app_store",
        "current_version": "23.25.84",
        "rating": 4.0,
        "total_reviews": 2500000,
        "category": "Social Networking"
    }
]

mock_reviews = [
    {
        "id": 1,
        "app_id": "com.whatsapp",
        "user_name": "João Silva",
        "content": "Excelente aplicativo! Muito fácil de usar e nunca trava.",
        "rating": 5,
        "sentiment": "positive",
        "sentiment_score": 0.95,
        "date": "2024-01-15"
    },
    {
        "id": 2,
        "app_id": "com.whatsapp",
        "user_name": "Maria Santos",
        "content": "App está muito lento e com muitos bugs na nova versão.",
        "rating": 1,
        "sentiment": "negative",
        "sentiment_score": 0.89,
        "date": "2024-01-14"
    },
    {
        "id": 3,
        "app_id": "com.whatsapp",
        "user_name": "Pedro Costa",
        "content": "Bom app, mas poderia ter mais funcionalidades.",
        "rating": 4,
        "sentiment": "positive",
        "sentiment_score": 0.72,
        "date": "2024-01-13"
    }
]

@app.route('/api/apps', methods=['GET'])
def get_apps():
    return jsonify(mock_apps)

@app.route('/api/apps/<app_id>', methods=['GET'])
def get_app(app_id):
    app = next((a for a in mock_apps if a['app_id'] == app_id), None)
    if app:
        return jsonify(app)
    return jsonify({'error': 'App não encontrado'}), 404

@app.route('/api/apps/<app_id>/reviews', methods=['GET'])
def get_app_reviews(app_id):
    app_reviews = [r for r in mock_reviews if r['app_id'] == app_id]
    return jsonify(app_reviews)

@app.route('/api/scraping/google-play/<app_id>', methods=['POST'])
def scrape_google_play(app_id):
    return jsonify({
        'message': 'Scraping simulado do Google Play',
        'app_id': app_id,
        'reviews_collected': 100,
        'status': 'success'
    })

@app.route('/api/scraping/apple-store/<app_id>', methods=['POST'])
def scrape_apple_store(app_id):
    return jsonify({
        'message': 'Scraping simulado da Apple Store',
        'app_id': app_id,
        'reviews_collected': 75,
        'status': 'success'
    })

@app.route('/api/sentiment/analyze', methods=['POST'])
def analyze_sentiment():
    return jsonify({
        'message': 'Análise de sentimentos simulada',
        'positive': 51.4,
        'neutral': 29.8,
        'negative': 18.8,
        'total_analyzed': 30000
    })

@app.route('/api/github/config', methods=['GET'])
def github_config():
    return jsonify({
        'github_service_available': False,
        'repo_name': 'Não configurado',
        'token_configured': False,
        'message': 'Configure GITHUB_TOKEN e GITHUB_REPO para usar automação'
    })

@app.route('/api/github/simulate-issue/<app_id>', methods=['POST'])
def simulate_issue(app_id):
    return jsonify({
        'message': 'Preview da issue gerado com sucesso',
        'preview': {
            'title': f'[WhatsApp] App crashando constantemente - 45 ocorrências reportadas',
            'body': '## 🚨 Alerta Automático: Tendência Negativa Detectada\n\n### 📱 Informações do Aplicativo\n- **Nome:** WhatsApp Messenger\n- **Versão:** 2.23.25.84\n- **Loja:** Google Play\n\n### 🔍 Problema Identificado\n**App crashando constantemente após a última atualização**\n\n### 📊 Estatísticas\n- **Frequência:** 45 ocorrências\n- **Confiança da IA:** 92.0%\n- **Tendência:** 📈 Increasing',
            'labels': ['bug', 'user-feedback', 'automated'],
            'would_create': True
        },
        'analysis': {
            'should_create_issue': True,
            'main_issue': 'crash',
            'frequency': 45,
            'confidence': 0.92
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'API de Análise de Apps funcionando',
        'version': '1.0.0'
    })

# Para Vercel
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

