import os
import sys

python_home = '/storage/www/apps/perso/venv'

activate_this = '%s/bin/activate_this.py' % python_home
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

root = os.path.dirname(os.path.abspath(__file__))
if root not in sys.path:
    sys.path.insert(0, root)

from app import create_app
application = create_app(os.getenv('APP_CONFIG') or 'production')
