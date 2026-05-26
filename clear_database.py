import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from web.models import init_db, clear_database


def main():
    init_db()
    clear_database()
    print("数据库已清空，系统已重置。")


if __name__ == "__main__":
    main()
