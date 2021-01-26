import sys

from partridge import create_app
from partridge.config import config

app = create_app( config )