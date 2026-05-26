import os
import time

from middleware.middleware_server import MiddlewareServer
from consumers.audit_consumer import AuditConsumer
from consumers.notice_consumer import NoticeConsumer
from consumers.stat_consumer import StatConsumer
from consumers.query_consumer import QueryConsumer
from web.app import create_app
from web.models import init_db
from utils.logger import ComponentLogger

ComponentLogger.initialize_log_dir()

def start_middleware():
    server = MiddlewareServer(host="127.0.0.1", port=5001)
    server.start_server()
    return server


def start_consumers():
    audit = AuditConsumer(host="127.0.0.1", port=5001)
    notice = NoticeConsumer(host="127.0.0.1", port=5001)
    stat = StatConsumer(host="127.0.0.1", port=5001)
    query = QueryConsumer(host="127.0.0.1", port=5001)

    audit.connect()
    audit.subscribe_topic("note/publish")
    audit.start_listening()

    notice.connect()
    notice.subscribe_topic("note/like")
    notice.subscribe_topic("note/comment")
    notice.start_listening()

    stat.connect()
    stat.subscribe_topic("note/like")
    stat.subscribe_topic("note/comment")
    stat.start_listening()

    query.connect()
    query.subscribe_topic("query/request")
    query.start_listening()

    return [audit, notice, stat, query]


if __name__ == "__main__":
    init_db()

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        server = start_middleware()
        consumers = start_consumers()
        time.sleep(0.5)

    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True, threaded=True)