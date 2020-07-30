import datetime as dt


def year(request):
    year = dt.datetime.today().year
    return {"year": year}
