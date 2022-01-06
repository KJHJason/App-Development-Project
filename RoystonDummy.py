from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import shelve, os, math, stripe
import Student, Teacher, Admin, Forms
from Security import password_manager, sanitise, validate_email
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path    