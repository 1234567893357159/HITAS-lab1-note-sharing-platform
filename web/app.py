import os
import sys
import uuid
from flask import Flask, render_template, request, redirect, url_for, make_response

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from producer.producer import MessageProducer
from producer.query_client import QueryClient
from web.models import init_db

producer = MessageProducer(host="127.0.0.1", port=5001)
query_client = QueryClient(host="127.0.0.1", port=5001)


def create_app():
    init_db()
    app = Flask(__name__, template_folder="templates", static_folder="static")

    @app.route("/")
    def index():
        """
        首页 - 获取所有笔记列表
        
        通过 QueryClient 向中间件发送查询请求，不直接访问数据库
        """
        result = query_client.query("get_notes")
        notes = result.get("data", []) if result.get("status") == "success" else []
        
        # 设置禁用缓存的响应头，确保每次访问都是最新数据
        resp = make_response(render_template("index.html", notes=notes))
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp

    @app.route("/note/<note_id>")
    def note_detail(note_id):
        """
        笔记详情页 - 获取笔记详情、评论和点赞数
        
        所有数据都通过 QueryClient 从中间件获取
        """
        note_result = query_client.query("get_note", {"note_id": note_id})
        note = note_result.get("data") if note_result.get("status") == "success" else None
        
        if not note:
            return redirect(url_for("index"))
        
        comments_result = query_client.query("get_comments", {"note_id": note_id})
        comments = comments_result.get("data", []) if comments_result.get("status") == "success" else []
        
        likes_result = query_client.query("get_like_count", {"note_id": note_id})
        likes = likes_result.get("data", 0) if likes_result.get("status") == "success" else 0
        
        return render_template("note_detail.html", note=note, comments=comments, likes=likes)

    @app.route("/add", methods=["GET", "POST"])
    def add_note():
        """
        添加笔记 - 通过中间件发送发布消息
        
        Flask 不直接访问数据库，只向中间件发送 note/publish 消息
        由 AuditConsumer 接收消息并保存到数据库
        """
        if request.method == "POST":
            note_id = str(uuid.uuid4())
            content = {
                "note_id": note_id,
                "title": request.form["title"],
                "content": request.form["content"],
                "author": request.form.get("author", "guest"),
                "created_at": request.form.get("created_at")
            }
            # 通过中间件发送消息，不直接调用数据库
            producer.send_message("note/publish", content)
            return redirect(url_for("index"))
        return render_template("add_note.html")

    @app.route("/note/<note_id>/like", methods=["POST"])
    def like_note(note_id):
        """
        点赞笔记 - 通过中间件发送点赞消息
        
        Flask 不直接访问数据库，只向中间件发送 note/like 消息
        由 NoticeConsumer 接收消息并保存到数据库
        """
        user_id = request.form.get("user_id", "guest")
        content = {
            "note_id": note_id,
            "user_id": user_id
        }
        # 通过中间件发送消息，不直接调用数据库
        producer.send_message("note/like", content)
        return redirect(url_for("note_detail", note_id=note_id))

    @app.route("/note/<note_id>/comment", methods=["POST"])
    def comment_note(note_id):
        """
        评论笔记 - 通过中间件发送评论消息
        
        Flask 不直接访问数据库，只向中间件发送 note/comment 消息
        由 NoticeConsumer 接收消息并保存到数据库
        """
        user_id = request.form.get("user_id", "guest")
        comment_text = request.form["comment_text"]
        content = {
            "note_id": note_id,
            "user_id": user_id,
            "comment_text": comment_text
        }
        # 通过中间件发送消息，不直接调用数据库
        producer.send_message("note/comment", content)
        return redirect(url_for("note_detail", note_id=note_id))

    @app.route("/note/<note_id>/delete", methods=["POST"])
    def delete_note_route(note_id):
        """
        删除笔记 - 通过中间件发送删除消息
        
        Flask 不直接访问数据库，只向中间件发送 note/delete 消息
        由消费者接收消息并删除数据库记录
        """
        content = {
            "note_id": note_id
        }
        # 通过中间件发送消息，不直接调用数据库
        producer.send_message("note/delete", content)
        
        # 短暂等待，确保异步删除操作完成
        import time
        time.sleep(0.1)
        
        # 重定向并设置禁用缓存的响应头，确保浏览器刷新页面
        resp = make_response(redirect(url_for("index")))
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp

    return app