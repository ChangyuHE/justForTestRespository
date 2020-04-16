from datetime import date, timedelta


def _number_of_weeks(year):
    weeks = [4, 4, 5, 4, 4, 5, 4, 4, 5, 4, 4, 5]
    jan1 = date(year, 1, 1)
    dec31 = date(year, 12, 31)

    if jan1.weekday() == 5:
        weeks[0] += 1
    if jan1.weekday() == 4 and dec31.weekday() == 5:
        weeks[10] += 1

    return weeks


def _first_sunday(year, month):
    d = date(year, 1, 1)
    if d.weekday() != 6:
        d -= timedelta(days=(1+d.weekday()))

    for _, n in zip(range(month-1), _number_of_weeks(year)):
        d += timedelta(weeks=n)

    return d


def ww_date(d=None):
    if not d:
        d = date.today()

    year = d.year
    if d >= _first_sunday(year+1, 1):
        year += 1

    year_starts_on = _first_sunday(year, 1)
    days = (d - year_starts_on).days

    week, day = divmod(days, 7)
    return year, week+1, day
