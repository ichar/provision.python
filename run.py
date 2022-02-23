import os
import sys

python_home = '/storage/www/apps'

app_path = '%s/perso' % python_home

activate_this = '%s/venv/bin/activate_this.py' % app_path
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

sys.path.insert(0, python_home)

root = os.path.dirname(os.path.abspath(__file__))
if root not in sys.path:
    sys.path.append(root)

from app import create_app
application = create_app(os.getenv('APP_CONFIG') or 'production')
