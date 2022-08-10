#!/usr/bin/env python

from flask import Flask           # import flask
app = Flask(__name__)             # create an app instance

APP_VERSION = "1.0.3u"

@app.route("/")                   # at the end point /
def hello():                      # call method hello
    return f"Hello World! Application version {APP_VERSION}"         # which returns "hello world" and version number
if __name__ == "__main__":        # on running python app.py
    app.run(host="0.0.0.0")