import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ── Security ──────────────────────────────────────
    SECRET_KEY              = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG                   = os.environ.get('DEBUG', 'True') == 'True'

    # ── Database ──────────────────────────────────────
    SQLALCHEMY_DATABASE_URI        = os.environ.get('DATABASE_URL', 'sqlite:///event_management.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── JWT Auth ──────────────────────────────────────
    JWT_SECRET_KEY            = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-me')
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # ── File Uploads ──────────────────────────────────
    UPLOAD_FOLDER      = os.path.join(BASE_DIR, '..', 'static', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

    # ── External APIs ─────────────────────────────────
    GEMINI_API_KEY    = os.environ.get('GEMINI_API_KEY', '')
    STABILITY_API_KEY = os.environ.get('STABILITY_API_KEY', '')