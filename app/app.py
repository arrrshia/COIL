from typing import Any
from flask import Flask, redirect, request
from markupsafe import escape
import requests
import os, sys, json
from http import HTTPStatus
import io
from cvat_sdk import make_client, models
from cvat_sdk.core.proxies.tasks import ResourceType, Task
from cvat_sdk.api_client import Configuration, ApiClient, exceptions
from cvat_sdk.api_client.models import *
import webbrowser
from celery import Celery
import importlib.util
import sys
app = Flask(__name__)
simple_app = Celery('simple_worker', broker='amqp://admin:mypass@rabbit:5672', backend='rpc://')

# var/lib/docker/volumes/f6ea3fb681c4a714de3e17cd23ee282e4be51a8f923fe8888c034ff94df4fcf1/_data
@app.route('/annotate/<tag>/<filename>/', methods=['POST','GET'])
def ello(tag, filename):
    app.logger.info("Annotating")
    z = simple_app.send_task('tasks.annotateFile', kwargs={'filename': f'{filename}', 'tag': f'{tag}'})
    app.logger.info(z.backend)
    return redirect("http://localhost:8080/", code=302)

@app.route('/cvat_task/<tag>/<filename>/', methods=['POST','GET'])
def hi(tag, filename):
    app.logger.info("Saving File")
    c = simple_app.send_task('tasks.saveAtDirectory', kwargs={'filename': f'{filename}', 'tag': f'{tag}'})
    app.logger.info(c.backend)
    return redirect("http://localhost:8000/", code=302)

@app.route('/tag/<tag>')
def createProjectInCvat(tag):
    app.logger.info("Creating directory ")
    a = simple_app.send_task('tasks.work', kwargs={'tag': f'{tag}'})
    app.logger.info(a.backend)
    app.logger.info("Creating project ")
    b = simple_app.send_task('tasks.projectCreate', kwargs={'tag': f'{tag}'})
    app.logger.info(b.backend)
    return redirect("http://localhost:8080/projects/", code=302)

@app.route('/tag/<tag>/filename/<filename>/tasks/<taskid>/', methods=['POST','GET'])
def createTask(tag,filename,taskid):
    e = simple_app.send_task('tasks.taskCreationWithProject', kwargs={'filename': f'{filename}', 'tag': f'{tag}', 'taskid': f'{taskid}'})
    app.logger.info(e.backend)
    #tasks.writeToFile(firstPath, task.id, filename)
    return redirect("http://localhost:8080/projects/", code=302)

@app.route('/simple_start_task')
def call_method():
    app.logger.info("Invoking Method ")
    r = simple_app.send_task('tasks.longtime_add', kwargs={'x': 1, 'y': 2})
    app.logger.info(r.backend)
    return r.id

@app.route('/simple_task_status/<task_id>')
def get_status(task_id):
    status = simple_app.AsyncResult(task_id, app = simple_app)
    print("Invoking Method ")
    return "Status of the Task " + str(status.state)

@app.route('/simple_task_result/<task_id>')
def task_result(task_id):
    result = simple_app.AsyncResult(task_id).result
    return "Result of the Task " + str(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
