from flask import Flask, render_template, request, redirect, url_for, session
# from flask_html import FlaskHTML
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# flask_html = FlaskHTML(app)

app.secret_key ="your_secret_key"

# 连接MySQL数据库
db = pymysql.connect(
    host="localhost",
    user="root",
    password="y112502",
    port=3306,
    database="blog"
)


# 首页
@app.route('/')
def index():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM posts JOIN users on posts.user_id=users.id ORDER BY created_at DESC")
    posts = cursor.fetchall()
    cursor.close()
    return render_template('index.html', posts=posts)

# @app.route("/")
# def welcome():
#     return render_template('welcome.html')

@app.route("/blog/my_blog")
def my_blog():
    user_id = session.get('user_id')
    cursor = db.cursor()
    cursor.execute("select * from posts join users on posts.user_id=users.id where users.id = '{0}' ".format(user_id))
    posts = cursor.fetchall()
    cursor.close()
    return render_template("my_blog.html",posts=posts)

# 注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        name = request.form['name']
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, name) VALUES (%s, %s, %s)",
                           (username, password, name))
            db.commit()
            session['username'] = username
            return redirect(url_for('login'))
        except:
            return render_template('register.html', error='用户名已存在')
    else:
        return render_template('register.html')


# 登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user[2], password):
            session['username'] = username
            session['user_id'] = user[0]  # 存储用户ID
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='用户名或密码错误')
    else:
        return render_template('login.html')

@app.route('/updatepwd',methods=['GET','POST'])
def updatepwd():
    if request.method == 'POST':
        password1 = generate_password_hash(request.form['password1'])
        password2 = request.form['password2']
        # print(password2)
        # print(password1)
        user_id = session.get('user_id')
        if user_id:
            if check_password_hash(password1, password2):
                cursor = db.cursor()
                cursor.execute("update users set password = '{0}' where id='{1}'".format(password1,user_id))
                db.commit()
                cursor.close()
                return redirect(url_for('index'))
            else:
                app.logger.error("两次密码不一样")
                return  redirect(url_for('updatepwd'))
        else:
            app.logger.error("用户未登录")
            return  redirect(url_for('login'))
    else:
        return render_template('updatepwd.html')


# 发布博客
@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
    #     user_id = session.get('user_id')
    #     if user_id:
    #         cursor = db.cursor()
    #         cursor.execute("INSERT INTO posts (title, body, user_id) VALUES (%s, %s, %s)", (title, body, user_id))
    #         db.commit()
    #         return redirect(url_for('index'))
    #     else:
    #         return redirect(url_for('login'))
    # else:
    #     return render_template('post.html')
        user_id = session.get('user_id')
        if user_id:
            app.logger.info('User {} is publishing a new blog'.format(user_id))
            cursor = db.cursor()
            cursor.execute("INSERT INTO posts (title, body, user_id) VALUES (%s, %s, %s)", (title, body, user_id))
            db.commit()
            return redirect(url_for('index'))
        else:
            app.logger.error('User is not logged in')
            return redirect(url_for('login'))
    else:
        return render_template('post.html')

# 发布评论
@app.route('/comment', methods=['POST'])
def comment():
    if request.method == 'POST':
        body = request.form['body']
        user_id = session.get('user_id')
        post_id = request.form['post_id']
        if user_id:
            cursor = db.cursor()
            cursor.execute("INSERT INTO comments (body, user_id, post_id) VALUES (%s, %s, %s)",
                           (body, user_id, post_id))
            db.commit()
            return redirect(url_for('post_detail', post_id=post_id))
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('index'))

@app.route("/blog/my_comment")
def my_comment():
        user_id = session.get("user_id")
        if user_id:
            cursor = db.cursor()
            cursor.execute("select * from posts join comments on posts.id=comments.post_id where comments.user_id='{0}' ORDER BY comments.created_at DESC".format(user_id))
            comments = cursor.fetchall()
            cursor.close()
            return render_template("my_comment.html",comments=comments)
        else:
            return render_template(url_for('login'))



# 博客详情页
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM posts join users on posts.user_id=users.id WHERE posts.id = %s", (post_id,))
    post = cursor.fetchone()
    cursor.execute("SELECT * FROM comments join users on comments.user_id = users.id  WHERE post_id = %s ORDER BY created_at DESC", (post_id,))
    comments = cursor.fetchall()
    return render_template('post_detail.html', post=post, comments=comments)

@app.route('/blog/myself')
def myself():
    user_id = session.get('user_id')
    if user_id:
        cursor = db.cursor()
        cursor.execute("select * from users where id = '{0}'".format(user_id))
        person = cursor.fetchone()
        cursor.close()
        return render_template("myself.html",person=person)
    else:
        return render_template(url_for('index'))

@app.route('/blog/chperson',methods=["GET","POST"])
def chperson():
    if request.method == 'POST':
        user_id = session.get('user_id')
        if user_id:
            name = request.form['name']
            cursor = db.cursor()
            cursor.execute("update users set name = '{0}' where id = '{1}'".format(name,user_id))
            db.commit()
            cursor.execute("select * from users where id = '{0}'".format(user_id))
            person = cursor.fetchone()
            db.commit()
            cursor.close()
            return render_template('myself.html',person=person)
        else:
            return render_template("index.html")
    else:
        return render_template("chperson.html")

# 退出登录
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=5000, debug=True)
