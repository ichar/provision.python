Setup python virtualenv and create a new one venv:

 $ cd /
 $ sudo pip3 install virtualenv

 $ cd /var/www/html/perso/
 $ sudo virtualenv venv
 $ ls -l

Check ip-address
----------------
local:

 $ hostname -I

public:
 $ curl -4 icanhazip.com

Check venv/bin/activate_this.py (!important)
--------------------------------------------
 $ sudo apt-get install apache2-dev

 $ sudo pip3 install pymssql==2.1.5
 $ sudo pip3 install mod_wsgi

 $ sudo find . -type d -exec chmod 755 {} \;
 $ sudo chown $USER:$USER perso/

 $ source venv/bin/activate

 $ (venv): pip --version
 $ (venv): pip install -r requirements.txt
 $ (venv): pip install -r reqnew.txt

 $ python3 -m compileall <pythonic-project-name>

Create Apache perso.conf (copy /var/www/html/perso/appache/perso.conf)
----------------------------------------------------------------------
 $ mod_wsgi-express module-config

Copy to perso.conf
------------------
LoadModule wsgi_module "/usr/local/lib/python3.8/dist-packages/mod_wsgi/server/mod_wsgi-py38.cpython-38-x86_64-linux-gnu.so"
WSGIPythonHome "/usr"

Add host (/etc/hosts)
---------------------
127.0.0.1   perso

 $ sudo a2ensite perso
 $ sudo systemctl reload apache2
 $ sudo systemctl status apache2.service

 $ sudo apt-get install libapache2-mod-wsgi-py3 apache2-dev
 $ sudo a2enmod wsgi

To remove anything (wsgi for instance) run:

 $ sudo apt-get purge --auto-remove libapache2-mod-wsgi-py3
 $ sudo apt-get autoremove

SSL/TLS with Apache:
--------------------

Look at /storage/www/apps/perso/apache (localhost, rosan).

 $ sudo a2enmod ssl
 $ sudo a2enmod headers
 $ sudo a2enconf ssl-params

Check /etc/ssl folder to valid apache sertificates.

 $ sudo a2ensite perso-ssl

Try to restart apache:

 $ sudo systemctl restart apache2

and open perso-link: 

https://perso
