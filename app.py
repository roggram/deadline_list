import os.path
import tornado.ioloop
import tornado.web
from pathlib import Path
import datetime
from pymongo import MongoClient

# mongoDBにアプリ側からデータを入れられるようにする
client = MongoClient("localhost:27017")

# GPTによるとこの関数はMongoDBからデータを取得するためのもの
def data():
  db = client["test_menta"]
  collection = db["tasks"]
  tasks = collection.find()
  return tasks

class MainHandler(tornado.web.RequestHandler):
  # GPTによるとメインページにアクセスした時の処理を行う
  def get(self):
    tasks = data()
    q = ""
    self.render("index.html", tasks=tasks, q=q)
  # GPTによるとメインページからフォームがPOSTされた時の処理を行う
  # どの基準でソートするかのスクリプトは以下のpostメソッドに記述
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
class PostTaskHandler(tornado.web.RequestHandler):
  def post(self):
    #↓のprintでパラメーターの確認ができます。
    print(self.get_argument('task'))
    print(self.get_argument('priority_order'))
    print(self.get_argument('deadline'))
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
    collection.insert_one(
      {"task":task, "priority_order":int(priority_order), "deadline":int(deadline), "sum":int(sum)}
    )
    #最後にリダイレクト。
    self.redirect("/")

class DeleteTaskHandler(tornado.web.RequestHandler):
  def post(self):
    # フォームから送信されたタスクのIDを取得
    task_id = self.get_argument("task_id")
    # MogoDBのObjectID型にtask_idを変換（必要に応じて）
    from bson.objectid import ObjectId
    task_id = ObjectId(task_id)
    # タスクをデータベースから削除
    db = client.test_menta
    collection = db.tasks
    collection.delete_one({"_id": task_id})
    # 削除後ユーザーをルートパスにリダイレクト
    self.redirect('/')

class EditTaskHandler(tornado.web.RequestHandler):
  def get(self):
    task_id = self.get_argument('task_id')
    from bson.objectid import ObjectId
    task_id = ObjectId(task_id)
    db = client.test_menta
    collection = db.tasks
    task = collection.find_one({'_id': task_id})
    self.render("edit_task.html", task = task)


class UpdateTaskHandler(tornado.web.RequestHandler):
    def post(self):
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
            {'_id': task_id},
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


application = tornado.web.Application([
  (r"/", MainHandler),
  (r"/post_task", PostTaskHandler),
  (r"/delete_task", DeleteTaskHandler),
  (r"/edit_task", EditTaskHandler),
  (r"/update_task", UpdateTaskHandler),
  ],
  # 以下の一文の意味がわかりません
  template_path=os.path.join(os.path.dirname(__file__), 'templates')
)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()