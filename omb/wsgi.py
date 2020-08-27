#!/usr/bin/env python
import sys

sys.path.insert(0, "/var/www/html/omb")

# use a different index for deploy
from index import server as application
