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
from pytz import timezone

import requests


app = Flask(__name__, static_url_path='/static')

app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'I hope this enough to be secret'

stations = ["32", "33", "34", "35", "36", "37", "52"]

@app.route('/', methods=['GET'])
def index():
	token = request.args.get('token')
	if token:
		s = requests.get("https://monitor.agropogoda.com/api/get_zonds_by_token?token=" + token).json()
	else:
		s = stations
	return render_template('index.html', stations=s, token=token)


@app.route('/get_info', methods=['GET'])
def statistics():
	station_number_default = request.args.get('station_number')
	start_date_default = request.args.get('start_date')
	end_date_default = request.args.get('end_date')
	token = request.args.get('token')

	if not station_number_default or not start_date_default or not end_date_default:
		abort(400)

	# date -> integer parsing
	try:
		sd = list(map(int, start_date_default.split('-')))
		ed = list(map(int, end_date_default.split('-')))
	except ValueError:
		abort(400)

	try:
		start_date = datetime.datetime(sd[0], sd[1], sd[2], 0, 0)
		end_date = datetime.datetime(ed[0], ed[1], ed[2], 0, 0)

		if start_date == end_date:
			end_date += datetime.timedelta(days=1)

		start_date = int(start_date.timestamp())
		end_date = int(end_date.timestamp())
	except ValueError:
		abort(400)

	if start_date > end_date:
		return "Начальная дата отчёта должна быть меньше конечной", 400

	if station_number_default not in stations:
		return "Неверный номер зонда", 400
	
	# valid station name in MySQL
	station_number = "600000" + station_number_default

	conn = mysql.connector.connect(
				user='public',
				password='StrongPassword123',
				host='agropogoda.com',
				port=22303,
				database='apik3')

	cursor = conn.cursor()

	query = ("select time, `1000`, `1005`, `1010`, `1015`, `1020`, `1030`, `1040`, `1050`, `1060` " +
			 " from `{0}` where time between '{1}' and '{2}';".format(
							station_number, start_date, end_date))

	cursor.execute(query)

	result = []
	for line in cursor:
		cur_datetime = datetime.datetime.fromtimestamp(line[0]).replace(tzinfo=timezone('UTC'))
		result.append(tuple([cur_datetime.date()] + list(line[1:10])))

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
		result_string += "<tr><td><b>" + date.strftime("%d.%m.%Y") + "</b></td>" + "<td></td>"*9 + "</tr>"

		result_string += "<tr>"
		result_string += "<td>" + "средняя t, °C" + "</td>"
		for elem in mean_t:
			result_string += "<td>" + str(round(elem, 2)) + "</td>"
		result_string += "</tr>"

		result_string += "<tr>"
		result_string += "<td>" + "min t, °C" + "</td>"
		for elem in min_t:
			result_string += "<td>" + str(round(elem, 2)) + "</td>"
		result_string += "</tr>"

		result_string += "<tr>"
		result_string += "<td>" + "max t, °C" + "</td>"
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

	last_mes_string = "<h5>Температура</h5>"
	for line in cursor:
		for h, elem in zip(heights, line[1:]):
			last_mes_string += "Результат на " + str(h) + " см: " + str(round(elem, 2)) + "<br>"

		# put timestamp
		collected_date = datetime.datetime.fromtimestamp(line[0]).replace(tzinfo=timezone('UTC'))
		last_mes_string += ("<hr> Данные за <br> " + str(collected_date.date().strftime("%d.%m.%Y"))
						+ " " + str(collected_date.time().strftime("%H:%M")))

	fig = plt.figure()
	ax = plt.axes()

	ax.set_xlabel('время (дни)')
	ax.set_ylabel('температура (°C)')

	# plot mean for each height by days
	means = np.array(means).transpose()
	for j in range(9):
		ax.plot(dates, means[j])
		plt.xticks(dates, rotation='vertical')

	means_file = 'static/img/temp/' + str(randint(10000, 99999)) + '.png'
	fig.savefig(means_file)


	fig_last_day = plt.figure()
	ax_last_day = plt.axes()

	ax_last_day.set_ylabel('температура (°C)')

	# plot temperatures for only last day
	for line in last_day.transpose():
		ax_last_day.plot([i for i in range(1, len(last_day)+1)], line)

	last_day_file = 'static/img/temp/' + str(randint(10000, 99999)) + '.png'
	fig_last_day.savefig(last_day_file)

	# beautify output
	last_day = ".".join(dates[::-1][0].split('-')[::-1])

	conn.close()

	back_link = "/?token=" + str(token) if token != 'None' else '/'

	return render_template('station_info.html', results=result_string,
							last_measurement=last_mes_string, 
							station_number=station_number_default,
							date='.'.join(start_date_default.split('-')[::-1]) + 
							" - " + '.'.join(end_date_default.split('-')[::-1]),
							means_file=means_file, last_day_file=last_day_file, 
							last_day=last_day, back_link=back_link)


if __name__ == '__main__':
    app.run(debug=True)
