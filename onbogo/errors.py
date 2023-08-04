# from functools import wraps
from flask import Blueprint, render_template, request, redirect, abort
errors = Blueprint('errors', __name__)

# from .models import User
from . import onbogo


@errors.app_errorhandler(404)
def error_404(err):
    print(err)
    return render_template("errors/404.html"), 404


@errors.app_errorhandler(405)
def error_405(err):
    print(err)
    return render_template("errors/405.html"), 405


@errors.app_errorhandler(500)
def error_500(err):
    print(err)
    return render_template("errors/500.html"), 500