from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class App(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    store = db.Column(db.String(20), nullable=False)  # 'google_play' ou 'app_store'
    current_version = db.Column(db.String(50))
    rating = db.Column(db.Float)
    total_reviews = db.Column(db.Integer)
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    icon_url = db.Column(db.String(500))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    reviews = db.relationship('Review', backref='app', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.String(100), db.ForeignKey('app.app_id'), nullable=False)
    user_name = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    sentiment = db.Column(db.String(20))  # 'positive', 'negative', 'neutral'
    sentiment_score = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    review_id = db.Column(db.String(100))  # ID único da review na loja

class AnalysisReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.String(100), db.ForeignKey('app.app_id'), nullable=False)
    total_reviews = db.Column(db.Integer)
    positive_count = db.Column(db.Integer)
    negative_count = db.Column(db.Integer)
    neutral_count = db.Column(db.Integer)
    avg_sentiment_score = db.Column(db.Float)
    main_issues = db.Column(db.Text)  # JSON string com principais problemas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

