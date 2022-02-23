#!/bin/sh
#gunicorn -w 4 run:application
gunicorn --certfile ssl/cert.pem --keyfile ssl/key.pem -b 0.0.0.0:8000 -w 4 run:application
