# -*- coding: utf-8 -*-

import sqlite3


class Database:
    def __init__(self, db_name, default_table=1):
        self.db_name = db_name
        self.default_table = default_table

        try:
            self.db = sqlite3.connect(db_name)
        except sqlite3.Error as e:
            raise Exception("Error connecting to database!")

        self.init_tables()

    def init_tables(self):
        # Profile Table
        self.add_table(
            table_name="Profile",
            user_id="INTEGER",
            operation_system="TEXT",
            desktop_environment="TEXT",
            desktop_themes="TEXT",
            web_browser="TEXT",
            code_editors="TEXT",
            terminal_software="TEXT",
            shell_software="TEXT",
            screenshot_url="TEXT",
        )

        # AvatarHistory Table
        self.add_table(
            table_name="AvatarHistory",
            user_id="INTEGER",
            avatar_url="TEXT",
            datetime="TIMESTAMP",
        )

    def add_table(self, table_name, **columns):
        self.cols = ""

        for col_name, col_type in columns.items():
            self.cols += "{} {},".format(col_name, col_type)

        self.cols = self.cols[0 : len(self.cols) - 1]
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS {}({})".format(table_name, self.cols)
        )

    def insert(self, table_name, *data):
        self.data = ""

        for value in data:
            self.data += '"{}",'.format(value)

        self.data = self.data[0 : len(self.data) - 1]
        self.db.execute(
            "INSERT INTO {} VALUES ({})".format(table_name, self.data)
        )
        self.db.commit()

    def add(self, insertion_type, table_name, **columns):
        if insertion_type == "table":
            self.cols = ""

            for col_name, col_type in columns.items():
                self.cols += "{} {},".format(col_name, col_type)

            self.cols = self.cols[0 : len(self.cols) - 1]
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS {}({})".format(
                    table_name, self.cols
                )
            )

    def remove(self, table_name, where: tuple):
        where = "{}={}".format(where[0], where[1])

        self.db.execute("DELETE FROM {} WHERE {}".format(table_name, where))
        self.db.commit()

    def update(self, table_name, where: tuple, **columns):
        self.cols = ""
        where = "{}={}".format(where[0], where[1])

        for col_name, col_item in columns.items():
            self.cols += "{}='{}',".format(col_name, col_item)

        self.cols = self.cols[0 : len(self.cols) - 1]
        self.db.execute(
            "UPDATE {} SET {} WHERE {}".format(table_name, self.cols, where)
        )
        self.db.commit()

    def get_item(self, table_name, where: tuple):
        where = "{}={}".format(where[0], where[1])

        self.items = self.db.execute(
            "SELECT * FROM {} WHERE {}".format(table_name, where)
        )
        self.db.commit()

        return list(self.items)

    def get_tables(self):
        self.tables = self.db.execute("SELECT name FROM sqlite_master")
        return list(self.tables)

    def check_item(self, table_name, where: tuple):
        return bool(self.get_item(table_name, where))

    def sql_do(self, *params):
        self.db.execute(*params)
        self.db.commit()

    def close_connection(self):
        self.db.close()
