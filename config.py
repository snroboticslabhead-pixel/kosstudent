import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    
    # MySQL configuration for PythonAnywhere
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'testingkostask.mysql.pythonanywhere-services.com'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'testingkostask'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'Kostask@532'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'testingkostask$default'
    
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # OpenRouter AI configuration for code validation and simulation
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY') or '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'
    OPENROUTER_MODEL = os.environ.get('OPENROUTER_MODEL') or 'openai/gpt-4o'
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"