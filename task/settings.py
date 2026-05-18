

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-39np(amtl$j5x!&na&75lvys*cik)3da6j_z%46f#-g609@47i'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'taskapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'task.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'task.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
JAZZMIN_SETTINGS = {

    "site_title": "Task-Management_system Admin",

    "site_header": "Task-Management_system Management",

    "site_brand": "Task-Management_system",

    "welcome_sign": "Welcome to Task-Management_system",

    "copyright": "Task-Management_system",

    "site_logo": "taskapp/img/admin-logo.svg",

    "login_logo_dark": "taskapp/img/admin-logo.svg",

    "show_sidebar": True,

    "navigation_expanded": True,

    "search_model": "taskapp.Cars",

    "custom_css": "taskapp/css/admin-dark.css",

    "custom_js": "taskapp/js/admin-theme-toggle.js",

    "show_ui_builder": False,

    "sidebar_fixed": True,

    "navbar_fixed": True,

    "layout_boxed": False,

    "sidebar_nav_compact_style": True,

    "sidebar_nav_flat_style": True,

    "no_navbar_border": True,

    "accent": "accent-info",

    "icons": {
        "taskapp.cars": "fas fa-car",
        "taskapp.mechanic": "fas fa-user-cog",
        "taskapp.task": "fas fa-tools",
        "auth.user": "fas fa-user",
        "auth.group": "fas fa-users",
    },

    "default_icon_parents": "fas fa-folder-open",

    "default_icon_children": "fas fa-circle",
}

JAZZMIN_UI_TWEAKS = {
    "theme": "cyborg",
    "dark_mode_theme": "flatly",
    "navbar": "navbar-dark navbar-primary",
    "sidebar": "sidebar-dark-primary",
    "accent": "accent-info",
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "layout_boxed": False,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_flat_style": True,
    "no_navbar_border": True,
}
