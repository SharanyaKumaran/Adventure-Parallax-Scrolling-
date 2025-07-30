from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Homepage with project information"""
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard for authenticated users"""
    return render_template('dashboard.html', user=current_user)

@main.route('/recognition')
@login_required
def recognition():
    """Real-time sign language recognition page"""
    return render_template('recognition.html', user=current_user)

@main.route('/training')
@login_required
def training():
    """Model training interface page"""
    return render_template('training.html', user=current_user)

@main.route('/about')
def about():
    """About page with project details"""
    return render_template('about.html')