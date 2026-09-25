import os
from pathlib import Path


# =========================================================
# Diretório principal do projeto
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================================
# Segurança
# =========================================================

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "troque-esta-chave-por-uma-chave-grande-e-secreta",
)

# Em produção, configure DJANGO_DEBUG=False.
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in {
    "1",
    "true",
    "yes",
}

ALLOWED_HOSTS = [
    "dcasgroup2810.pythonanywhere.com",
    "localhost",
    "127.0.0.1",
]

CSRF_TRUSTED_ORIGINS = [
    "https://dcasgroup2810.pythonanywhere.com",
]


# =========================================================
# Aplicativos instalados
# =========================================================

INSTALLED_APPS = [
    # O Unfold precisa vir antes do django.contrib.admin.
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Aplicações do projeto
    "chamados",
]


# =========================================================
# Aparência do painel administrativo
# =========================================================

UNFOLD = {
    "SITE_TITLE": "Central de Tecnologia",
    "SITE_HEADER": "Central de Tecnologia",
    "SITE_SUBHEADER": "Chamados e gestão de equipamentos",
    "SITE_SYMBOL": "support_agent",
    "SITE_URL": "/",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SHOW_BACK_BUTTON": True,
    "SHOW_UI_WARNINGS": True,
    "BORDER_RADIUS": "10px",
}


# =========================================================
# Middlewares
# =========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]


# =========================================================
# URLs e WSGI
# =========================================================

ROOT_URLCONF = "helpdesk.urls"

WSGI_APPLICATION = "helpdesk.wsgi.application"


# =========================================================
# Templates
# =========================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# =========================================================
# Banco de dados
# =========================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# =========================================================
# Validação de senhas
# =========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# =========================================================
# Idioma e fuso horário
# =========================================================

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_TZ = True


# =========================================================
# Arquivos estáticos
# =========================================================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = []

if (BASE_DIR / "static").exists():
    STATICFILES_DIRS.append(BASE_DIR / "static")


# =========================================================
# Arquivos enviados pelos usuários
# =========================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# =========================================================
# Login e logout
# =========================================================

LOGIN_URL = "/login/"

LOGIN_REDIRECT_URL = "/"

LOGOUT_REDIRECT_URL = "/login/"


# =========================================================
# Configurações gerais
# =========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MIDDLEWARE = [*MIDDLEWARE, 'chamados.acessos.AdminRoleMiddleware']

TEMPLATES[0]['OPTIONS']['context_processors'].append('chamados.notificacoes.contexto')
HELPDESK_EMAIL_ENABLED = False
EMAIL_TIMEOUT = 5

EMAIL_HOST = 'email-ssl.com.br'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = 'marco.oliveira@dcasgroup.com'
DEFAULT_FROM_EMAIL = 'DCAS HelpDesk <marco.oliveira@dcasgroup.com>'
