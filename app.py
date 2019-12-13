from flask import abork
from flask import Flask
from flask import redirect
from flask import request
from flask import render_template
from flask import session

import mysql.connector
import matplotlib as plt

app = Flask(__name__)


@app.route('/', methods=['GET'])
def hello():
	# TODO: main page
    return "Fine"


@app.route('/login', methods=['GET', 'POST'])
def login(name):
	# TODO: return login page
    return "Login"


@app.route('/register', methods=['GET', 'POST'])
def register(name):
	# TODO: return register page
    return "Register"


@app.route('/<int:station_number>', methods=['GET'])
def statistics(name):
	# TODO: return statistics on station
    return "Statistics"


if __name__ == '__main__':
    app.run()
    