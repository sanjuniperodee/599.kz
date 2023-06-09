from .settings.base import *

env_name = os.getenv('.env', 'local')

if env_name == 'production':
    from .settings.production import *
elif env_name == 'development':
    from .settings.development import *
