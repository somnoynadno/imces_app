from flask import abort
from flask import Flask
from flask import redirect
from flask import request
from flask import render_template
from flask import session
from flask import url_for

import datetime
import mysql.connector

import numpy as np
import pandas as pd
import matplotlib as plt
import datetime

app = Flask(__name__, static_url_path='/static')

app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'I hope this enough to be secret'


@app.route('/', methods=['GET'])
def index():
	# TODO: main page
	if not 'username' in session:
		return redirect(url_for('login'), 302)
	else:
		return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = str(request.form.get('username'))
		password = str(request.form.get('password'))

		if not username or not password:
			return "Wrong credentials", 400

		try:
			conn = mysql.connector.connect(
		         user=username,
		         password=password,
		         host='imces.ru',
		         port=22303,
		         database='apik3')
			conn.close()
			
		except Exception:
			return "No such user or incorrect password", 400

		session['username'] = username

		return redirect(url_for('index'), 302)
	else:
		return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
	# TODO: return register page
	if not 'username' in session:
		return redirect(url_for('login'), 302)

	return "Register"


@app.route('/get_info', methods=['GET'])
def statistics():
	if not 'username' in session:
		return redirect(url_for('login'), 302)

	station_number = request.args.get('station_number')
	start_date = request.args.get('start_date')
	end_date = request.args.get('end_date')

	sd = list(map(int, start_date.split('-')))
	ed = list(map(int, end_date.split('-')))

	start_date = int(datetime.datetime(sd[0], sd[1], sd[2], 0, 0).timestamp())
	end_date = int(datetime.datetime(ed[0], ed[1], ed[2], 0, 0).timestamp())

	print(station_number, start_date, end_date)

	if not station_number or not start_date or not end_date:
		abort(400)

	station_number = "600000" + station_number

	conn = mysql.connector.connect(
         user='Fomin',
         password='VvbrKYKj',
         host='imces.ru',
         port=22303,
         database='apik3')

	cursor = conn.cursor()

	# query = "show tables;"
	query = ("select time, `1000`, `1005`, `1010`, `1015`, `1020`, `1030`, `1040`, `1050`, `1060` " +
			 " from `{0}` where time between '{1}' and '{2}';".format(
							station_number, start_date, end_date))
	print(query)
	cursor.execute(query)

	result = []
	for line in cursor:
		result.append(tuple([datetime.datetime.fromtimestamp(line[0]).date()] + list(line[1:9])))
		# print(line)

	res = np.array(result)
	# print(res)

	temp = []
	i = 0
	while i < len(res):
		date = res[i][0]
		print(date)
		temp.append(res[i][1:])
		i += 1
		while res[i][0] == date:
			temp.append(res[i][1:])
			i += 1
			if i == len(res):
				break

		temp = np.array(temp)
		temp_frame = pd.DataFrame(data=temp, dtype=np.float)

		print(temp_frame.head())
		print(temp_frame.describe(include='all'))

		temp = []

	conn.close()
	return render_template('station_info.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
