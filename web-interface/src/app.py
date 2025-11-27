from flask import Flask, request, session, render_template, redirect, url_for, flash
import os
import datetime

app = Flask(__name__)
FLAG = open("/flag.txt", "r").read()
app.secret_key = FLAG + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@app.route('/', methods=['GET'])
def index():
    username = None
    if 'username' in session:
        username = session['username']
    return render_template('index.html', username=username)

@app.route('/profile', methods=['GET'])
def profile():
    if 'username' in session:
        if session['username'] == 'admin':
            return render_template('user.html', username=session['username'], flag=FLAG)
        else:
            return render_template('user.html', username=session['username'])
    else:
        return redirect(url_for('login_user'))

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        path = '/home/' + username
        if not os.path.exists(path):
            flash('User not found')
            return redirect(url_for('login_user'))
        
        try:
            with open(path + '/password.txt', 'r') as f:
                if password == f.read():
                    session['username'] = username
                    return redirect(url_for('profile'))
                else:
                    flash('Incorrect password')
                    return redirect(url_for('login_user'))
        except Exception as e:
            flash(str(e))
            return redirect(url_for('login_user'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        question = request.form['question']
        answer = request.form['answer']
        if "password" in question:
            flash("Question cannot contain 'password'")
            return redirect(url_for('register'))
        path = '/home/' + username
        if os.path.exists(path):
            flash('User already exists')
            return redirect(url_for('register'))
        
        os.mkdir(path)
        
        with open(path + '/password.txt', 'w') as f:
            f.write(password)
        os.mkdir(path + '/questions')
        with open(path + "/questions/" + question, 'w') as f:
            f.write(answer)
        return redirect(url_for('login_user'))
    
@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'GET':
        return render_template('forgot.html')
    elif request.method == 'POST':
        username = request.form['username']
        path = '/home/' + username
        if not os.path.exists(path):
            flash('User not found')
            return redirect(url_for('forgot'))
        try:
            questions = os.listdir(path + '/questions')
            flash("Here is your password question to recovery: " + str(questions))
            return redirect(url_for('recover'))
        except Exception as e:
            flash(str(e))
            return redirect(url_for('forgot'))
    
@app.route('/recover', methods=['GET', 'POST'])
def recover():
    if request.method == 'GET':
        return render_template('recover.html')
    elif request.method == 'POST':
        username = request.form['username']
        question = request.form['question']
        answer = request.form['answer']
        path = '/home/' + username
        if not os.path.exists(path):
            flash('User not found')
            return redirect(url_for('recover'))
        
        try:
            questions = os.listdir(path + '/questions')
            for q in questions:
                if (q == question):
                    with open(path + '/questions/' + question, 'r') as f:
                        if answer == f.read():
                            with open(path + '/password.txt', 'r') as pa:
                                flash("Your password is: " + pa.read())
                                if username == 'admin':
                                    for q in questions: 
                                        os.remove(path + '/questions/' + q)
                                return redirect(url_for('login_user'))
            flash("Answer is incorrect")
            return redirect(url_for('recover'))
        except Exception as e:
            flash(str(e))
            return redirect(url_for('recover'))
            


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1337, threaded=True)