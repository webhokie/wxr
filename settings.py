#!/usr/bin/env python
#! -*- coding: utf-8 -*-

"""
Project Configuration File.

Simulate INI file format but use python syntax instead.
"""

#>> [database]
DB_HOST = '127.0.0.1'     # database server address
DB_PORT = 3306            # database server port
DB_USER = 'root'          # database user
DB_PASS = 'rootpwd'          # database user's password
DB_NAME = 'party'         # database name to use
DB_CHARSET = 'utf8'       # database charset to use


#>> [logging]
LOG_LEVEL = 'DEBUG'
