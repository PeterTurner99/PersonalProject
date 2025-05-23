from datetime import timedelta
from math import ceil
from django.db.models import Q
from django.forms.models import model_to_dict
from collections import defaultdict


def date_range(start_date, length):
    for n in range(length):
        yield start_date + timedelta(days=n)


def tasks_from_date_range(start_date, length, user):
    from menu_generator.models import RepeatingTask

    repeating_tasks = RepeatingTask.objects.filter(user=user).order_by('time')
    non_daily_task = repeating_tasks.filter(~Q(frequency='d'))
    daily_tasks = repeating_tasks.filter(frequency='d')
    date_dictionary = defaultdict(list)
    for date in date_range(start_date, length):
        for repeating_task in non_daily_task:
            if repeating_task.matching_date(date):
                date_dictionary[date.isoformat()].append(model_to_dict(repeating_task))
        for daily_task in daily_tasks:
            date_dictionary[date.isoformat()].append(model_to_dict(daily_task))
    return date_dictionary


def week_of_month(date):
    first_date = date.replace(day=1)
    day_of_month = date.day
    adjusted_day_of_month = day_of_month + first_date.weekday()
    return int(ceil(adjusted_day_of_month / 7.0))
