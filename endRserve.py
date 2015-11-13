#!/usr/bin/env python
import pyRserve
try:
    conn = pyRserve.connect()
    conn.shutdown()
except:
    pass  # Failure will mean Rserve is not running
