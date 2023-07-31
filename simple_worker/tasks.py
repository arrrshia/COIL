from typing import Any
import requests
import json
from cvat_sdk import make_client, models
from cvat_sdk.core.proxies.tasks import ResourceType, Task
from cvat_sdk.api_client import Configuration, ApiClient, exceptions
from cvat_sdk.api_client.models import *
import os, io
from util import make_pbar
import time
from celery import Celery
from celery.utils.log import get_task_logger
from dotenv import load_dotenv

logger = get_task_logger(__name__)

app = Celery('tasks',
             broker='amqp://admin:mypass@rabbit:5672',
             backend='rpc://')
load_dotenv()
x=os.environ.get('username')
y=os.environ.get('password')
if x is None:
    x = "andrewalmasi@gmail.com"
if y is None:
    y = "Hunt77584$"

@app.task()
def longtime_add():
    logger.info('Work Finished')
    logger.info(x)
    return x

@app.task
def annotateFile(filename, tag):
    firstPath = os.path.join(os.getcwd(), tag)
    isExist = os.path.exists(firstPath)
    logger.info(isExist)
    logger.info(firstPath)
    with open(firstPath + r'/indexing.txt', 'r') as f:
        for index, line in enumerate(f):
            if filename in line:
                doesExist = True
                taskid = int(line.split(" ")[1])
                break
    payload = json.dumps({"username": x,"email": x,"password": y})
    headers= {'accept': 'application/vnd.cvat+json','Content-Type':'application/json'}
    r = requests.request("POST", 'http://cvat-server:8080/api/auth/login', headers=headers, data=payload)
    logger.info("Done signing in")
    headers = {'accept': 'application/vnd.cvat+json',}
    jobidresult = requests.get('http://cvat-server:8080/api/tasks/{}'.format(taskid), headers=headers, cookies=r.cookies).json()
    jobid = jobidresult["data"]
    logger.info("Done getting jobid")

    headers = {'accept': 'application/vnd.cvat+json','Content-Type': 'application/json','X-CSRFTOKEN': r.cookies['csrftoken'],}
    json_data = {
        'function': 'openvino-omz-public-yolo-v3-tf',
        'task': taskid,
        'job': jobid,
        'quality': 'original',
        'cleanup': False,
        'convMaskToPoly': False,
        'threshold': 0,
        'max_distance': 0,
    }
    response = requests.post('http://cvat-server:8080/api/lambda/requests', cookies=r.cookies, headers=headers, json=json_data)
    return "Successful"

with make_client(host="http://cvat-server:8080", credentials=(x,y)) as client:
    @app.task
    def saveAtDirectory(filename,tag):
        firstPath = os.path.join(os.getcwd(), tag)
        isExist = os.path.exists(firstPath)
        if not isExist:
            return "Task Data has not been (at least successfully) exported by CVAT"
        with open(firstPath + r'/indexing.txt', 'r') as f:
            for index, line in enumerate(f):
                if filename in line:
                    doesExist = True
                    taskid = int(line.split(" ")[1])
                    break
        if not doesExist:
            return "Task Data has not been (at least successfully) exported by CVAT"

        pbar_out = io.StringIO()
        pbar = make_pbar(file=pbar_out)
        path = os.getcwd() + f"/{tag}" f"/task_{taskid}-cvat.zip"
        task = client.tasks.retrieve(taskid)
        task.export_dataset(
            format_name="CVAT for images 1.1",
            filename=path,
            pbar=pbar,
            include_images=True,
        )
        assert "100%" in pbar_out.getvalue().strip("\r").split("\r")[-1]
        return "Task has been exported by CVAT successfully"



    @app.task
    def work(tag):
        firstPath = os.path.join(os.getcwd(), tag)
        isExist = os.path.exists(firstPath)
        if not isExist:
            os.mkdir(firstPath)
            open(firstPath+f"/indexing.txt", 'w')
        return firstPath

    @app.task
    def projectCreate(tag):
        projects = client.projects.list()
        if any(p.name == tag for p in projects):
            for p in projects:
                if p.name == tag:
                    project = p
                    break
        else:
            project = client.projects.create(spec=models.ProjectWriteRequest(name=tag))
        firstPath = os.getcwd()
        if os.path.exists(os.path.join(firstPath, 'celeryManagement.txt')):
            with open(firstPath + f"/celeryManagement.txt", 'a') as f:
                f.write(tag + " " + str(project.id) + "\n")
        else:
            with open(firstPath + f"/celeryManagement.txt", 'w') as f:
                f.write(tag + " " + str(project.id) + "\n")
        return project.id

    @app.task
    def taskCreationWithProject(filename,tag,taskid):
        logger.info('Starting work ')
        with open(os.getcwd() + r'/celeryManagement.txt', 'r') as f:
            for index, line in enumerate(f):
                if tag in line:
                    projectid = line.split(" ")[1]
                    break
        task: Any = client.tasks.create_from_data(
                spec={
                "name": f"{filename}",
                "project_id": int(projectid),
                },
                resource_type=ResourceType.LOCAL,
                resources=['/var/lib/docker/volumes/webodm_appmedia/_data/project/{}/task/{}/{}'.format(tag,taskid,filename)],
            )
        with open(os.getcwd() + f"/{tag}" + f"/indexing.txt", 'a') as f:
            f.write(filename + " " + str(task.id) + "\n")
        logger.info('Finished work ')
        return task.id