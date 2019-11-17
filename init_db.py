import sqlite3
from hashlib import sha256
import sys
import tqdm


def init_tables():
	connection = sqlite3.connect("users.sqlite")
	cursor = connection.cursor()
	query = "PRAGMA foreign_keys = ON;"
	cursor.execute(query)
	query = "DROP TABLE IF EXISTS privileges;"
	cursor.execute(query)
	query = "DROP TABLE IF EXISTS users;"
	cursor.execute(query)
	query = """
	CREATE TABLE users(
		id INTEGER PRIMARY KEY,
		username TEXT NOT NULL UNIQUE,
		password_hash TEXT CHECK(LENGTH(password_hash) == 64) NOT NULL DEFAULT "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
	);
	"""
	cursor.execute(query)
	query = """
	CREATE TABLE privileges(
		id INTEGER PRIMARY KEY,
		username TEXT,
		privilege TEXT CHECK(privilege IN ("SELECT",  "INSERT", "UPDATE", "DELETE")) NOT NULL,
		FOREIGN KEY (username)
			REFERENCES users (username)
				ON DELETE RESTRICT
				ON UPDATE CASCADE
	);
	"""
	cursor.execute(query)
	connection.commit()
	connection.close()

	connection = sqlite3.connect("data.sqlite")
	cursor = connection.cursor()
	query = "PRAGMA foreign_keys = ON;"
	cursor.execute(query)
	query = "DROP TABLE IF EXISTS addresses;"
	cursor.execute(query)
	query = "DROP TABLE IF EXISTS people;"
	cursor.execute(query)
	query = """
	CREATE TABLE people(
		id INTEGER PRIMARY KEY,
		full_name TEXT NOT NULL UNIQUE,
		telephone VARCHAR(12) UNIQUE
	);
	"""
	cursor.execute(query)
	query = """
	CREATE TABLE addresses(
		id INTEGER PRIMARY KEY,
		user_id INT NOT NULL,
		street VARCHAR(30) NOT NULL,
		city VARCHAR(30) NOT NULL,
		state VARCHAR(30) NOT NULL,
		FOREIGN KEY (user_id)
			REFERENCES people (id)
				ON DELETE RESTRICT
				ON UPDATE CASCADE
	);
	"""
	cursor.execute(query)
	connection.commit()
	connection.close()


def init_users():
	connection = sqlite3.connect("users.sqlite")
	cursor = connection.cursor()

	query = "INSERT INTO users (username, password_hash) VALUES (?, ?);"

	cursor.execute(query, ("admin", sha256(b"admin").hexdigest()))
	cursor.execute(query, ("selecter", sha256(b"selecter").hexdigest()))
	cursor.execute(query, ("updater", sha256(b"updater").hexdigest()))
	cursor.execute(query, ("deleter", sha256(b"deleter").hexdigest()))
	cursor.execute(query, ("inserter", sha256(b"inserter").hexdigest()))

	query = "INSERT INTO privileges (username, privilege) VALUES (?, ?);"

	cursor.execute(query, ("admin", "SELECT"))
	cursor.execute(query, ("admin", "INSERT"))
	cursor.execute(query, ("admin", "UPDATE"))
	cursor.execute(query, ("admin", "DELETE"))

	cursor.execute(query, ("selecter", "SELECT"))

	cursor.execute(query, ("updater", "SELECT"))
	cursor.execute(query, ("updater", "UPDATE"))

	cursor.execute(query, ("deleter", "SELECT"))
	cursor.execute(query, ("deleter", "DELETE"))

	cursor.execute(query, ("inserter", "SELECT"))
	cursor.execute(query, ("inserter", "INSERT"))

	connection.commit()
	connection.close()


def init_data():
	import requests
	from bs4 import BeautifulSoup as BS
	connection = sqlite3.connect("data.sqlite")
	cursor = connection.cursor()
	try:
		n = int(sys.argv[1])
	except:
		n = 20
	for i in tqdm.tqdm(range(1, n+1)):
		r = requests.get("https://fakepersongenerator.com/?new=fresh")
		soup = BS(r.text, "lxml")
		name = soup.find("div", {"class": "col-md-4 col-sm-6 col-xs-12"}).contents[1].text
		phone = soup.find("div", {"class": "col-md-8 col-sm-6 col-xs-12"}).contents[5].contents[1].text
		query = "INSERT INTO people (full_name, telephone) VALUES (?, ?);"
		cursor.execute(query, (name, phone))
		street = soup.find("div", {"class": "col-md-8 col-sm-6 col-xs-12"}).contents[3].contents[1].text
		city, state = soup.find("div", {"class": "col-md-8 col-sm-6 col-xs-12"}).contents[4].contents[1].text.split(", ")[:2]
		query = "INSERT INTO addresses (user_id, street, city, state) VALUES (?, ?, ?, ?);"
		cursor.execute(query, (i, street, city, state))
	connection.commit()
	connection.close()


def main():
	init_tables()
	init_users()
	init_data()


if __name__ == "__main__":
	main()