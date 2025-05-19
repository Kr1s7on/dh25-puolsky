from flask import Blueprint

usage = Blueprint('usage', __name__)

from . import views  # noqa
