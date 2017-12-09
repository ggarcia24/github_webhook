from .base import *

INTERNAL_IPS = [
    '127.0.0.1',
    '192.168.1.13'
]

ALLOWED_HOSTS += [
    'localhost',
    '127.0.0.1',
    'github_webhook',
    'github_webhook.local',
    'github_webhook.local.',
    '.local',
    '.local.'
]

INSTALLED_APPS += (
    'debug_toolbar',
)

MIDDLEWARE = MIDDLEWARE + [
    'debug_toolbar.middleware.DebugToolbarMiddleware'
]
