# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

# Python modules
import os, logging 

# Flask modules
from flask               import render_template, request, url_for, redirect, send_from_directory
from flask_login         import login_user, logout_user, current_user, login_required
from werkzeug.exceptions import HTTPException, NotFound, abort
from werkzeug.utils import secure_filename
import numpy as np

# App modules
from app        import app, lm, db, bc
from app.models import User
from app.forms  import LoginForm, RegisterForm, ImageForm
from ultralytics import YOLO
# Provide login manager with load_user callback
@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/de')
def de():
    return render_template('pages/form.html')

@app.route('/upload', methods=['POST'])
def upload():
    filenew = request.files['image']
    filedirname = os.path.join(os.path.dirname(__file__), app.config['UPLOAD_FOLDER'], secure_filename(filenew.filename))
    filenew.save(filedirname)
    model = YOLO(os.path.join(os.path.dirname(__file__),app.config['STATIC_BEST']))
    # model = YOLO('yolov8x.pt')
    otcm = model.predict(source=filedirname, save=True)
    names = otcm[0].names
    classList = []
    l = 0
    for result in otcm:
        boxes = result.boxes  # Boxes object for bbox outputs
        masks = result.masks  # Masks object for segmenation masks outputs
        probs = result.probs 
    for i in range(len(boxes)):
        print('i is ', i)
        ar = boxes[i]
        classList.append(names[int(ar.cls)] + ' ' +str(ar.conf.item()))
    return str(result)

@app.route('/detect.html', methods=['GET','POST'])
def detect():
    '''detect'''

    form = ImageForm(request.form)

    msg = None

    if request.method == 'GET': 

        return render_template('layouts/auth-default.html',
                                content=render_template( 'pages/form.html', form=form, msg=msg ) )

    # check if both http method is POST and form is valid on submit
    if request.method == 'POST':
        filenew = request.files['image']
        filenew.save(os.path.join(os.path.dirname(__file__), app.config['UPLOAD_FOLDER'], secure_filename(filenew.filename)))
        # assign form data to variables
        msg = request.form.get('texts', '', type=str)
        return render_template('layouts/auth-default.html',
                                content=render_template( 'pages/form.html', form=form, msg=msg ) )

    # return render_template('layouts/auth-default.html',
    # content=render_template( 'pages/form.html', task = request.form['filenames']) )
    # if request.method == 'GET':
        
    

# Logout user
@app.route('/logout.html')
def logout():
    ''' Logout user '''
    logout_user()
    return redirect(url_for('index'))

# Reset Password - Not 
@app.route('/reset.html')
def reset():
    ''' Not implemented ''' 
    return render_template('layouts/auth-default.html',
                            content=render_template( 'pages/reset.html') )

# Register a new user
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    ''' Create a new user '''

    # declare the Registration Form
    form = RegisterForm(request.form)

    msg = None

    if request.method == 'GET': 

        return render_template('layouts/auth-default.html',
                                content=render_template( 'pages/register.html', form=form, msg=msg ) )

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 
        email    = request.form.get('email'   , '', type=str) 

        # filter User out of database through username
        user = User.query.filter_by(user=username).first()

        # filter User out of database through username
        user_by_email = User.query.filter_by(email=email).first()

        if user or user_by_email:
            msg = 'Error: User exists!'
        
        else:         

            pw_hash = password #bc.generate_password_hash(password)

            user = User(username, email, pw_hash)

            user.save()

            msg = 'User created, please <a href="' + url_for('login') + '">login</a>'     

    else:
        msg = 'Input error'     

    return render_template('layouts/auth-default.html',
                            content=render_template( 'pages/register.html', form=form, msg=msg ) )

# Authenticate user
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    
    # Declare the login form
    form = LoginForm(request.form)

    # Flask message injected into the page, in case of any errors
    msg = None

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 

        # filter User out of database through username
        user = User.query.filter_by(user=username).first()

        if user:
            
            #if bc.check_password_hash(user.password, password):
            if user.password == password:
                login_user(user)
                return redirect(url_for('index'))
            else:
                msg = "Wrong password. Please try again."
        else:
            msg = "Unknown user - Please register." 

    return render_template('layouts/auth-default.html',
                            content=render_template( 'pages/login.html', form=form, msg=msg ) )

# App main route + generic routing
@app.route('/', defaults={'path': 'form.html'})
@app.route('/<path>')
def index(path):

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    content = None

    try:
        return render_template('layouts/default.html',
                                content=render_template( 'pages/'+path) )
    except:
        return render_template('layouts/auth-default.html',
                                content=render_template( 'pages/error-404.html' ) )

# Return sitemap 
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'sitemap.xml')



