from .base import *

env_name = os.getenv('.env', 'local')

if env_name == 'prod':
    from .production import *
elif env_name == 'local':
    from .development import *
