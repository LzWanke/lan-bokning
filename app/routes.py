from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, BookingForm, \
    ResetPasswordRequestForm, ResetPasswordForm, PostForm
from app.models import User, Post, Table ##Table behövs för att kunna importera dess data
from app.email import send_password_reset_email


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = BookingForm()    #Variabel för formen som finns i forms.py


    if form.validate_on_submit():

        try:
            if int(form.tableInt.data) <= 47 and int(form.tableInt.data) >= 1:  #Verifierar att användaren inte tar något bordsnummer som inte finns i kartan
                table = Table(tableInt=int(form.tableInt.data), isBooked=True, username=current_user.username)  #Den här variabeln ger datan som sedan ska läggas till i databasen
                db.session.add(table)   #Lägg till i databasen
                db.session.commit()     #Uppdatera databasen med ny data
                flash('Du har nu bokat ett bord')   ## Nu funkar allt bra
            else:   ##om användaren skirver in t.ex. 56 kommer den här köras
                flash('Det finns ingen plats som heter så')
        except: #Om det blir helt fel, t.ex. om användaren skirver in bokstäver i formen, så hamnar man här, därför att formens data konverteras till int
            flash('Bokningen kunde inte slutföras, kolla att du inte tar en upptagen plats!')
        return redirect(url_for('index'))##användaren skickas tll hemsidan
    tableInfo = Table.query.order_by(Table.tableInt).all()  #variabel som har värderna i modelen Table

    return render_template('index.html', title='Home', form=form, tableInfo=tableInfo)  #visar hemsidan och skickar med information som kan användas med jinja2




@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Grattis, du är registerad')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Kolla i dit mail efter instruktioner över hur du byter lösenord')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/admin', methods=['POST', 'GET'])
@login_required
def admin():
    if request.method == 'GET': #GET därför att jag vill åt informationen
        bokningar = Table.query.order_by(Table.tableInt).all()  ##variabel för alla bord
        return render_template('admin.html', bokningar=bokningar)

@app.route('/delete/<int:id>')
def delete(id):
    bort = Table.query.get_or_404(id)   ##hämtar id på den man vill ta bort, om id inte finns/gäller blir det error 404

    try:
        db.session.delete(bort) ##Istället för db.session.add så är det db.session.delete
        db.session.commit()     ##uppdaterar databasen om ny data
        return redirect('/admin')   #skickar användaren tillbaka till admin panelen ifall denne vill ta bort en till
    except:
        return redirect('/')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))
