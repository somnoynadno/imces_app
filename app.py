from flask import abort
from flask import Flask
from flask import redirect
from flask import request
from flask import render_template
from flask import session
from flask import url_for

import datetime
import mysql.connector

# runtime fix
import matplotlib
matplotlib.use('Agg')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime

from random import randint

app = Flask(__name__, static_url_path='/static')

app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'I hope this enough to be secret'


@app.route('/', methods=['GET'])
def index():
	if not 'username' in session:
		return redirect(url_for('login'), 302)
	else:
		return render_template('index.html', username=session['username'])


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = str(request.form.get('username'))
		password = str(request.form.get('password'))

		if not username or not password:
			return "Wrong credentials", 400

		# user must exist in database
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


@app.route('/get_info', methods=['GET'])
def statistics():
	if not 'username' in session:
		return redirect(url_for('login'), 302)

	station_number_default = request.args.get('station_number')
	start_date_default = request.args.get('start_date')
	end_date_default = request.args.get('end_date')

	if not station_number_default or not start_date_default or not end_date_default:
		abort(400)

	# date -> integer parsing
	try:
		sd = list(map(int, start_date_default.split('-')))
		ed = list(map(int, end_date_default.split('-')))
	except ValueError:
		abort(400)

	try:
		start_date = int(datetime.datetime(sd[0], sd[1], sd[2], 0, 0).timestamp())
		end_date = int(datetime.datetime(ed[0], ed[1], ed[2], 0, 0).timestamp())
	except ValueError:
		abort(400)

	if start_date > end_date:
		return "The end date must be less than the start date", 400

	stations = ("32", "33", "36", "37")
	if station_number_default not in stations:
		return "Invalid station number", 400
	
	# valid station name in MySQL
	station_number = "600000" + station_number_default

	conn = mysql.connector.connect(
				user='Fomin',
				password='VvbrKYKj',
				host='imces.ru',
				port=22303,
				database='apik3')

	cursor = conn.cursor()

	query = ("select time, `1000`, `1005`, `1010`, `1015`, `1020`, `1030`, `1040`, `1050`, `1060` " +
			 " from `{0}` where time between '{1}' and '{2}';".format(
							station_number, start_date, end_date))

	cursor.execute(query)

	result = []
	for line in cursor:
		result.append(tuple([datetime.datetime.fromtimestamp(line[0]).date()] + list(line[1:10])))

	# array of measurements for each timestamp
	res = np.array(result)

	i = 0
	temp  = []
	means = []
	dates = []
	result_string = ""

	# store data for each day in temp variable
	while i < len(res)-1:
		# get current date
		date = res[i][0]
		temp.append(res[i][1:])
		i += 1

		while res[i][0] == date:
			# append same date results
			temp.append(res[i][1:])
			i += 1
			if i == len(res):
				break
			
		temp = np.array(temp)
		temp_frame = pd.DataFrame(data=temp, dtype=np.float)
		last_day = temp

		# count this values for each height in this day
		mean_t = temp_frame.describe(include='all').as_matrix()[1]
		min_t  = temp_frame.describe(include='all').as_matrix()[3]
		max_t  = temp_frame.describe(include='all').as_matrix()[7]

		means.append(mean_t)
		dates.append(str(date)[5:])

		# making result string to render it in template
		result_string += "<tr><td><b>" + str(date) + "</b></td>" + "<td></td>"*9 + "</tr>"

		result_string += "<tr>"
		result_string += "<td>" + "mean T, °C" + "</td>"
		for elem in mean_t:
			result_string += "<td>" + str(round(elem, 2)) + "</td>"
		result_string += "</tr>"

		result_string += "<tr>"
		result_string += "<td>" + "min T, °C" + "</td>"
		for elem in min_t:
			result_string += "<td>" + str(round(elem, 2)) + "</td>"
		result_string += "</tr>"

		result_string += "<tr>"
		result_string += "<td>" + "max T, °C" + "</td>"
		for elem in max_t:
			result_string += "<td>" + str(round(elem, 2)) + "</td>"
		result_string += "</tr>"

		# ready to heandle next day
		temp = []

	# get the last measurement of the station
	last_mes_query = ("select time, `1000`, `1005`, `1010`, `1015`, `1020`, `1030`, `1040`, `1050`, `1060` " +
			 		  " from `{0}` order by time desc limit 1;".format(station_number))

	cursor.execute(last_mes_query)
	heights = [0, 5, 10, 15, 20, 30, 40, 50, 60]

	last_mes_string = "<h5>Temperature</h5>"
	for line in cursor:
		for h, elem in zip(heights, line[1:]):
			last_mes_string += "Result on " + str(h) + "sm:" + str(round(elem, 2)) + "<br>"

		# put timestamp
		collected_date = datetime.datetime.fromtimestamp(line[0])
		last_mes_string += "<hr> Collected at: <br> " + str(collected_date.date()) + " " + str(collected_date.time())

	fig = plt.figure()
	ax = plt.axes()

	# plot mean for each height by days
	means = np.array(means).transpose()
	for j in range(9):
		ax.plot(dates, means[j])
		plt.xticks(dates, rotation='vertical')

	means_file = 'static/img/temp/' + str(randint(10000, 99999)) + '.png'
	fig.savefig(means_file)


	fig_last_day = plt.figure()
	ax_last_day = plt.axes()

	# plot temperatures for only last day
	for line in last_day.transpose():
		ax_last_day.plot([i for i in range(len(last_day))], line)

	last_day_file = 'static/img/temp/' + str(randint(10000, 99999)) + '.png'
	fig_last_day.savefig(last_day_file)

	# beautify output
	last_day = ".".join(dates[::-1][0].split('-')[::-1])

	conn.close()
	return render_template('station_info.html', results=result_string,
							last_measurement=last_mes_string, 
							station_number=station_number_default,
							date=start_date_default + " - " + end_date_default,
							means_file=means_file, last_day_file=last_day_file,
							username=session['username'], last_day=last_day)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
