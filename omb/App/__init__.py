"""
in-memory dataset is loaded from init
"""

from .. import backend


dataset = backend.Dataset()

from .playground import test_app
from .homepage import home_app
from .app import app

