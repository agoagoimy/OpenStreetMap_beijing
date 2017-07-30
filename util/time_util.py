import arrow

def date_to_datetime(data):
	return arrow.get(date).format('YYYY-MM-DD HH:mm:ss ZZ')

def datetime_to_date(datetime):
	return arrow.get(datetime).format('YYYY-MM-DD')

def now():
	return arrow.now()
