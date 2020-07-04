#!/usr/bin/env python
import sys

print(sys.version)
print(sys.version_info)

sys.path.insert(0, "/var/www/html/omb")

# use a different index for deploy
from index_for_deploy import server as application
