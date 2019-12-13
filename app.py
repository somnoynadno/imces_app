from flask import abort
from flask import Flask
from flask import redirect
from flask import request
from flask import render_template
from flask import session
from flask import url_for

import datetime
import mysql.connector

import matplotlib as plt

app = Flask(__name__, static_url_path='/static')

app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'I hope this enough to be secret'


@app.route('/', methods=['GET'])
def index():
	# TODO: main page
	if not 'username' in session:
		return redirect(url_for('login'), 302)
	else:
		return "OK"


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')

		if not username or not password:
			return "Wrong credentials", 400

		session['username'] = username

		return redirect(url_for('index'), 302)
	else:
		return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
	# TODO: return register page
    return "Register"


@app.route('/get_info/<int:station_number>', methods=['GET'])
def statistics(station_number	):
	conn = mysql.connector.connect(
         user='Fomin',
         password='VvbrKYKj',
         host='imces.ru',
         port=22303,
         database='apik3')

	cursor = conn.cursor()

	query = "show tables;"
	cursor.execute(query)

	result = []
	for line in cursor:
		result.append(line)

	conn.close()

	return str(result)


if __name__ == '__main__':
    app.run(debug=True)
