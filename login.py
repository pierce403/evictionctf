# https://medium.com/@perwagnernielsen/getting-started-with-flask-login-can-be-a-bit-daunting-in-this-tutorial-i-will-use-d68791e9b5b5

@app.route('/protected')
@login_required
def protected():
    return "protected area"

@login_manager.user_loader
def load_user(email):
    return User.query.filter_by(email = email).first()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if request.method == 'GET':
        return render_template('signup.html', form = form)
    elif request.method == 'POST':
      if form.validate_on_submit():
            if User.query.filter_by(email=form.email.data).first():
                return "Email address already exists" 
            else:
                newuser = User(form.email.data, form.password.data)
                db.session.add(newuser)
                db.session.commit()
                login_user(newuser)
                return "User created!!!"        
      else:
             return "Form didn't validate"

@app.route('/login', methods=['GET','POST'])
def login():
    form = SignupForm()
    if request.method == 'GET':
        return render_template('login.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            user=User.query.filter_by(email=form.email.data).first()
            if user:
                if user.password == form.password.data:
                    login_user(user)
                    return "User logged in"                
                else:
                    return "Wrong password"            
            else:
                return "user doesn't exist"        
    else:
            return "form not validated"

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return "Logged out"
