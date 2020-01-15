import datetime


def long_to_date(time):
    date = datetime.datetime.today.strftime('%Y-%m-%d') if time == 0 else datetime.datetime.fromtimestamp(
        time / 1e3)
    return date
