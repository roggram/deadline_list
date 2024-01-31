# データベース名はtest_menta
# コレクション名はtasks

import os.path
import tornado.ioloop
import tornado.web
from pathlib import Path
import datetime
# 道添以下一行を追加
from pymongo import MongoClient

# mongoDBにアプリ側からデータを入れられるようにする
client = MongoClient("localhost:27017")

def data():
  db = client["test_menta"]
  collection = db["tasks"]
  tasks = collection.find()
  return tasks

# ("/") にアクセスした時に以下
class MainHandler(tornado.web.RequestHandler):
  def get(self):
    tasks = data()
    q = ""
    self.render("index.html", tasks=tasks, q=q)

  def post(self):
    tasks = data()
    q = self.get_argument('q')
    print(q)
    if q == "desc":
      tasks = sorted(tasks, key=lambda o:o['registration_date'])
    elif q == "asc":
      #tasksをcreated_atの値をキーとして降順に並べる
      tasks = sorted(tasks, key=lambda o:o['deadline'])
    self.render("index.html", tasks=tasks, q=q)


# ("/tasks") にアクセスした時に以下
class TasksHandler(tornado.web.RequestHandler):
  def post(self):
    #↓のprintでパラメーターの確認ができます。
    print(self.get_argument('task'))
    print(self.get_argument('registration_date'))
    print(self.get_argument('deadline'))
    #ここからDBに登録する。

    # ↓フォームから送信されたデータを各変数に格納
    task = self.get_argument("task")
    registration_date = self.get_argument("registration_date")
    deadline = self.get_argument("deadline")

    # ↓データベースにフォームから受け取った値を挿入
      # test_mentaデータベースを取得
    db = client.test_menta
      # データベース内のtasksコレクションを取得
    collection = db.tasks
      # tasksコレクションにフォームで受け取ったデータを、辞書っぽく挿入
    collection.insert_one(
      {"task":task, "registration_date":registration_date, "deadline":deadline}
    )


    #最後にリダイレクト。
    self.redirect("/")

application = tornado.web.Application([
  (r"/", MainHandler),
  (r"/tasks", TasksHandler)
  ],
  # 以下の一文の意味がわかりません
  template_path=os.path.join(os.path.dirname(__file__), 'templates')
)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
