#!/usr/bin/env python
#! -*- coding: utf-8 -*-

import MySQLdb

import settings


"""
Database interface which supply the basic and common database access operations.
"""

#>> Decorators
def checkConnectionDecorator(func):
	"""
		Reconnect if connection is lost
	"""
	def wrapper(*args, **kwargs):
		self = args[0]
		try:
			self.connection.ping()
		except:
			self.reconnect()
		return func(*args, **kwargs)
	return wrapper

class DbError(Exception):
	"""
		Exception raised when database operation error occured.

		Attributes:
			message -- detail description about the error occured
	"""

	def __init__(self, message):
		"""
			Provide a message to describe the exception occured.

			@param message: detail description about the exception occured
		"""
		self.message = message

	def __str__(self):
		"""
			@return: detail description about the exception occured
		"""
		return repr(self.message)

class MySQL(object):
	"""
		Database Interface Implementation Using MySQLdb.
	"""

	def __init__(self, host=None, user=None, password=None, db=None, port=None, charset=None):
		"""
			Initialize a connection to mysql database server.

			Use the parameters if specified else use the database settings in the config file.

			@param host: database server address
			@param user: database server user
			@param password: database server user's password
			@param db: database name to use
			@param port: database server service port
			@param charset: database server charset
		"""
		if host is None:
			host = settings.DB_HOST
		if port is None:
			port = settings.DB_PORT
		if user is None:
			user = settings.DB_USER
		if password is None:
			password = settings.DB_PASS
		if db is None:
			db = settings.DB_NAME
		if charset is None:
			charset = settings.DB_CHARSET

		self.host = host
		self.port = port
		self.user = user
		self.password = password
		self.db = db
		self.charset = charset

		self.connection = None
		self.cursor = None

		self.reconnect()

	def reconnect(self):
		"""
			Connect to the specified database server.
		"""
		try:
			self.cursor.close()
			self.connection.close()
		except:
			pass

		try:
			self.connection = MySQLdb.connect(host=self.host, 
											  port=self.port, 
											  user=self.user, 
											  passwd=self.password, 
											  db=self.db, 
											  charset=self.charset)
		except MySQLdb.Error as e:
			raise DbError("MySQL Error %d: %s" % (e.args[0], e.args[1]))
		else:
			self.connection.autocommit(True)
			self.cursor = self.connection.cursor(MySQLdb.cursors.DictCursor)

	def select(self, sql):
		"""
			Execute `select` 

			Usage: select("select * from test where name='HanJunwei'")
				   select("select * from test where age>20")

			@param sql: select statement to execute
			@return: list of records with each record as dict type or None if no records match
		"""
		affectedRows = self._execute(sql)
		if affectedRows == 0:
			return None
		return self.cursor.fetchall()

	def selectCondition(self, table, where=None):
		"""
			Execute `select` based on table name and condition

			Usage: selectCondition('test', "age=26")
				   selectCondition('test', "name='HanJunwei'")

			@param table: table name to operate on
			@param where: where clause as a string
		"""

		if where is None:
			where = "true"
		sql = """SELECT * FROM `%s` WHERE %s""" % (table, where)
		return self.select(sql)

	def insert(self, sql):
		"""
			Execute `insert`

			Usage: insert("insert into test (name, age) values ('HanJunwei', 20)")

			@param sql: insert statement to execute
			@return: number of rows inserted, normally 1
		"""
		return self._execute(sql)

	def insertCondition(self, table, data):
		"""
			Execute `insert` based on provided conditions

			Usage: insertCondition('test', {'name': 'HanJunwei', 'age': 20})

			@param table: table name to operate on
			@param data: a dict whose key is column name and value is column value
			@return: number of rows inserted, normally 1
		"""
		fields = []
		values = []
		for key, value in data.iteritems():
			fields.append(key)
			values.append("'%s'" % value)
		sql = """INSERT INTO `%s` (%s) VALUES (%s)""" % (table, ", ".join(fields), ", ".join(values))
		return self.insert(sql)

	def insertMany(self, table, fields, values):
		"""
			Execute `insert` based on provided conditions

			Usage: insertMany('test', ('name', 'age'), [('HanJunwei', 20), ('XiaoHui', 20)])

			@param table: table name to operate on
			@param fields: a list or tuple consist of field names
			@param values: a list/tuple of list/tuple with each inner list/tuple as a record
			@return: number of rows inserted
		"""
		if len(fields) != len(values[0]):
			raise DbError("all value in values must have %s fields" % len(fields))

		fieldsInfo = ", ".join(fields)
		valuesInfo = ", ".join(["%s"] * len(fields))
		sql = """ INSERT INTO `%s` (%s) VALUES (%s)""" % (table, fieldsInfo, valuesInfo)
		return self.cursor.executemany(sql, values)

	def update(self, sql):
		"""
			Execute `update`

			Usage: update("update test set age=22 where name='HanJunwei'")

			@param sql: sql to be executed
		"""
		return self._execute(sql)

	def updateCondition(self, table, data, where=None):
		"""
			Execute `update` based on provided conditions

			Usage: update('test', {'age': 30}, "name='HanJunwei'")

			@param table: table name to operate on
			@param data: a dict whose key is field name and value is field value
			@param where: where clause default None
		"""
		setClause = ", ".join(["%s='%s'" % (key, value) for key, value in data.iteritems()])
		if where is None:
			where = "true"
		sql = """UPDATE `%s` SET %s WHERE %s""" % (table, setClause, where)
		return self._execute(sql)

	def delete(self, sql):
		"""
			Execute `delete`

			Usage: delete("delete from test where name='HanJunwei'")

			@param sql: sql to execute
		"""
		return self._execute(sql)

	def deleteCondition(self, table, where=None):
		"""
			Execute `delete` based on provided conditions

			Usage: deleteCondition('test', "name='HanJunwei'")

			@param table: table name to operate on
			@param where: where clause default None
		"""
		if where is None:
			where = "true"
		sql = """DELETE FROM `%s` WHERE %s""" % (table, where)
		return self._execute(sql)

	@checkConnectionDecorator
	def _execute(self, sql):
		try:
			return self.cursor.execute(sql)
		except MySQLdb.Error as e:
			raise DbError("MySQL Error: %s\nSQL: %s" % (e, sql))

	@checkConnectionDecorator
	def startTransaction(self):
		"""
			Start a transaction by turn autocommit to false.
		"""
		self.connection.autocommit(False)

	@checkConnectionDecorator
	def commitTransaction(self):
		"""
			Commit a transaction and turn autocommit to true.
		"""
		self.connection.commit()
		self.connection.autocommit(True)

	@checkConnectionDecorator
	def rollbackTransaction(self):
		"""
			Rollback a transaction and turn autocommit to true
		"""
		self.connection.rollback()
		self.connection.autocommit(True)





