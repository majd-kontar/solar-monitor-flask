import os
from urllib.parse import urlparse

url = urlparse(
    os.environ['DATABASE_URL']
)
user = url.username
password = url.password
database = url.path[1:]
host = url.hostname
port = url.port
