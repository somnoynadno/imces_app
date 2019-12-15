import requests

# fault-tolerance test script

def main():
	login_data =  {'username':'Fomin', 'password':'VvbrKYKj'}
	s = requests.Session()

	s.post('http://192.168.100.175:5000/login', login_data)


	for i in range(100):
		r = s.get('http://192.168.100.175:5000/get_info?station_number=32&start_date=2019-12-01&end_date=2019-12-13')

		print(r.status_code)
		if r.status_code != 200:
			print(r.text)


if __name__ == "__main__":
	main()