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
# ですので今回はmongoDB側の作業を行う前の段階でテンプレート側以外でエラーが起きていない状態を作ればOKです

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
      tasks = sorted(tasks, key=lambda o:o['created_at'], reverse=True)
    elif q == "asc":
      #tasksをcreated_atの値をキーとして降順に並べる
      tasks = sorted(tasks, key=lambda o:o['created_at'])
    self.render("index.html", tasks=tasks, q=q)

application = tornado.web.Application([
  (r"/", MainHandler),
  ],
  template_path=os.path.join(os.path.dirname(__file__), 'templates')
)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
