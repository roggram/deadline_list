import os.path
import tornado.ioloop
import tornado.web
from pathlib import Path
import datetime
from pymongo import MongoClient
import bcrypt

# mongoDBにアプリ側からデータを入れられるようにする
client = MongoClient("localhost:27017")
db = client["test_menta"]

# GPTによるとこの関数はMongoDBからデータを取得するためのもの
def data():
  db = client["test_menta"]
  collection = db["tasks"]
  tasks = collection.find()
  return tasks

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user_id(self):
        username = self.get_secure_cookie("user")
        if username:
            user = db.users.find_one({"username": username.decode('utf-8')})
            if user:
                return str(user["_id"])  # MongoDBのObjectIdを文字列に変換して返す
        return None
    
    def get_current_user(self):
        return self.get_secure_cookie("user")

class MainHandler(BaseHandler):
  # GPTによるとメインページにアクセスした時の処理を行う
  def get(self):
    user_id = self.get_current_user_id()  # 現在ログインしているユーザーのIDを取得
    if user_id:
        # ログインしているユーザーに紐づくタスクのみを取得
        tasks = db.tasks.find({"user_id": user_id})
    else:
        tasks = []
    self.render("index.html", tasks=tasks, q="")
    # 旧コード
    # tasks = data()
    # q = ""
    # self.render("index.html", tasks=tasks, q=q)
  # GPTによるとメインページからフォームがPOSTされた時の処理を行う
  # どの基準でソートするかのスクリプトは以下のpostメソッドに記述
  @tornado.web.authenticated
  def post(self):
    tasks = data()
    # 選択された方法に応じてソート処理
    q = self.get_argument('q')
    print(q)
    if q == "priority_order":
      tasks = sorted(tasks, key=lambda o:o['priority_order'],reverse=True)
    elif q == "deadline_order":
      tasks = sorted(tasks, key=lambda o:o['deadline'],reverse=True)
    elif q == "sum":
      tasks = sorted(tasks, key=lambda o:o['sum'],reverse=True)
    self.render("index.html", tasks=tasks, q=q)

# ("/tasks") にアクセスした時に以下
# GPT：ユーザーからの新しいタスク入力を処理しデータベースに記述
class PostTaskHandler(BaseHandler):
  @tornado.web.authenticated
  def post(self):
    #↓のprintでパラメーターの確認ができます。
    print(self.get_argument('task'))
    print(self.get_argument('priority_order'))
    print(self.get_argument('deadline'))
    user_id = self.get_current_user_id() # このメソッドは実装する必要があります
    #フォームからデータを受け取り、各変数に代入
    task = self.get_argument("task")
    priority_order = self.get_argument("priority_order")
    deadline = self.get_argument("deadline")
    sum = int(priority_order) + int(deadline)
    #データベースに入力された値を挿入
      # test_mentaデータベース、コレクションを取得
    db = client.test_menta
    collection = db.tasks
    # DBに辞書っぽく挿入
    collection.insert_one({
       "user_id": user_id,
       "task":task, 
       "priority_order":int(priority_order), 
       "deadline":int(deadline), 
       "sum":int(sum)}
    )
    #最後にリダイレクト。
    self.redirect("/")

class DeleteTaskHandler(BaseHandler):
  @tornado.web.authenticated
  def post(self):
    user_id = self.get_current_user_id()  # 現在ログインしているユーザーのIDを取得
    # フォームから送信されたタスクのIDを取得
    task_id = self.get_argument("task_id")
    # MogoDBのObjectID型にtask_idを変換（必要に応じて）
    from bson.objectid import ObjectId
    task_id = ObjectId(task_id)
    # タスクをデータベースから削除
    db = client.test_menta
    collection = db.tasks
    collection.delete_one({"_id": task_id, "user_id": user_id})
    # 削除後ユーザーをルートパスにリダイレクト
    self.redirect('/')

class EditTaskHandler(BaseHandler):
  @tornado.web.authenticated
  def get(self):
    user_id = self.get_current_user_id()  # 現在ログインしているユーザーのIDを取得
    task_id = self.get_argument('task_id')
    from bson.objectid import ObjectId
    task_id = ObjectId(task_id)
    db = client.test_menta
    collection = db.tasks
    task = collection.find_one({'_id': task_id, "user_id": user_id})
    if task:
       self.render("edit_task.html", task=task)
    else:
       self.redirect("/")

class UpdateTaskHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        user_id = self.get_current_user_id()
        task_id = self.get_argument('task_id')
        from bson.objectid import ObjectId
        task_id = ObjectId(task_id)
        task = self.get_argument('task')
        priority_order = self.get_argument('priority_order')
        deadline = self.get_argument('deadline')
        sum = int(priority_order) + int(deadline)

        # MongoDBのタスクドキュメントを更新
        db = client.test_menta
        collection = db.tasks
        collection.update_one(
            {'_id': task_id, "user_id": user_id},# ログインしているユーザーに紐づくタスクのみを更新
            {'$set': 
                {
                    'task': task,
                    'priority_order': int(priority_order),
                    'deadline': int(deadline),
                    'sum': int(sum),
                }
            }
        )
        
        # タスク一覧ページへリダイレクト
        self.redirect('/')

# ユーザー登録の処理
class RegisterHandler(BaseHandler):
  def get(self):
    self.render("register.html") #ユーザー登録フォームのテンプレート

  def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password").encode('utf-8')
        #？？
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        
        # ユーザー名が既に存在するかチェック
        if db.users.find_one({"username": username}):
            self.write("すでに登録されています")
        else:
            db.users.insert_one({"username": username, "password": hashed_password})
            self.redirect("/login")  # 登録成功後、ログインページにリダイレクト
  
# ログインの処理
class LoginHandler(BaseHandler):
  def get(self):
      self.render("login.html")  # ログインフォームのテンプレート

  def post(self):
      username = self.get_argument("username")
      password = self.get_argument("password").encode('utf-8')
      user = db.users.find_one({"username": username})
      
      if user and bcrypt.checkpw(password, user["password"]):
          self.set_secure_cookie("user", username)
          self.redirect("/")  # ログイン成功後、ホームページにリダイレクト
      else:
          self.write("Username or password is incorrect.")

class LogoutHandler(BaseHandler):
  @tornado.web.authenticated
  def get(self):
      self.clear_cookie("user")
      self.redirect("/login")  # ログアウト後、ログインページにリダイレクト

settings = {
  "cookie_secret": "YOUR_SECRET_KEY",
  "template_path": os.path.join(os.path.dirname(__file__), "templates"),
  "login_url": "/login",
}

application = tornado.web.Application([
  (r"/", MainHandler),
  (r"/post_task", PostTaskHandler),
  (r"/delete_task", DeleteTaskHandler),
  (r"/edit_task", EditTaskHandler),
  (r"/update_task", UpdateTaskHandler),
  (r"/register", RegisterHandler),
  (r"/login", LoginHandler),
  (r"/logout", LogoutHandler),
  ],**settings) # 修正：settings辞書をApplicationの引数として展開する


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()