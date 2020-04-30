import logging
import re

import django
from django.contrib.auth import authenticate
from django.shortcuts import redirect, render

from .models import CustomUser


def get_logger():
    logger = logging.getLogger('views_account')
    logger.setLevel(logging.DEBUG)
    logger_ch = logging.StreamHandler()
    logger_ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger_ch.setFormatter(formatter)
    logger.addHandler(logger_ch)

    return logger


log = get_logger()

username_pattern = re.compile('^[a-zA-Z0-9_.-]+$')
password_pattern = re.compile('^[A-Za-z0-9@#$%^&+=]+$')

# sprawdź czy użytkownik się zalogował
def check_login(request):
    if request.method == 'POST':
        body = request.POST
        username = body['username'].lower()
        password = body['password']
        next_url = body['next']

        user = authenticate(username=username, password=password)

        # złe dane logowania
        if user is None:
            return render(request, 'registration/login.html',
                          context={'username': username,
                                   'password': password,
                                   'error_login': 'Invalid credentials',
                                   'next': next_url})
        else:
            django.contrib.auth.login(request, user)

            if next_url:
                return redirect(next_url)
            else:
                return redirect('index')


def check_regex(pattern, to_check):
    if pattern.match(to_check):
        return True
    else:
        return False


def check_signup(request):
    if request.method == 'POST':
        body = request.POST
        username = body['username'].strip()
        password = body['password'].strip()
        next_url = body['next']

        if CustomUser.objects.filter(username=username):
            return render(request, 'registration/login.html',
                          context={'error_signup': 'Użytkownik już istnieje',
                                   'next': next_url})
        elif not check_regex(username_pattern, username):
            return render(request, 'registration/login.html',
                          context={'error_signup': 'not ^[a-zA-Z0-9_.-]+$ user',
                                   'next': next_url})
        elif not check_regex(password_pattern, password):
            return render(request, 'registration/login.html',
                          context={'error_signup': 'not ^[A-Za-z0-9@#$%^&+=]+$ password',
                                   'next': next_url})
        else:
            user = CustomUser(username=username)
            user.set_password(password)
            user.save()

            django.contrib.auth.login(request, user)

            if next_url:
                return redirect(next_url)
            else:
                return redirect('index')
