from flask import Flask
from flask import request
import boto3
import json
import time
import os
import sys

app = Flask(__name__)
s3bucket = sys.argv[1]

@app.route("/")
def hello():
    return "Yo."

@app.route("/new")
def new():
    return '''
<html>
<body>
<form action="/create_poll" method="get" enctype="multipart/form-data" >
  <input type="text" name="poll_name"><br>
  <textarea name="options" rows="10" cols="30"></textarea><br>
  <input type="submit">
</form>
</body>
</html>
'''

@app.route("/create_poll")
def create_poll():
    poll_name = request.args.get('poll_name', '')
    s3 = boto3.resource('s3')
    s3.Bucket(s3bucket).put_object(Key=poll_name + '/poll.json', Body=json.dumps(request.args.get('options','').split()))
    return "Poll created at /poll/" + poll_name

def read_from_s3(poll_name, remote_file):
    local_file_name = remote_file + ".tmp"
    boto3.client('s3').download_file('watchtower123', poll_name + '/' + remote_file, local_file_name)
    f = open(local_file_name, "r")
    content = json.loads(f.read())
    f.close()
    os.remove(local_file_name)
    return content

@app.route("/poll/<poll_name>")
def view_poll(poll_name=None):
    options = read_from_s3(poll_name, 'poll.json')
    page = '''
<html>
<body>
<form action="/vote/'''
    page = page + poll_name
    page = page + '''" method="get" enctype="multipart/form-data" >
'''
    for option in options:
        page = page + '<p>' + option + ': '+ '<input type="text" name="' + option + '"></p>'
    page = page + '''
  <input type="submit">
</form>
</body>
</html>
'''
    return page

@app.route("/vote/<poll_name>")
def vote(poll_name=None):
    s3 = boto3.resource('s3')
    s3.Bucket(s3bucket).put_object(Key=poll_name + '/vote.' + str(time.time()) + '.json', Body=json.dumps(request.args))
    return "Vote received"
    
@app.route("/count/<poll_name>")
def count(poll_name=None):
    return "done."

if __name__ == "__main__":
    app.run()
    #view_poll("cbc1")
    #print(read_from_s3("cbc_april", "poll.json"))
