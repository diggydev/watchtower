# Requires the following env variables to be set:
# AWS_ACCESS_KEY_ID
# AWS_SECRET_ACCESS_KEY
# AWS_S3_BUCKET

from flask import Flask
from flask import request
from flask import render_template
import boto3
import json
import time
import os
import sys
import counter

app = Flask(__name__)
s3bucket = os.environ['AWS_S3_BUCKET']

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
    body_string = '{{"name": "{}", "options": {}}}'.format(poll_name, json.dumps(request.args.get('options','').split('*')))
    s3.Bucket(s3bucket).put_object(Key=poll_name + '/poll.json', Body=body_string)
    return "Poll created at /poll/" + poll_name

def read_from_s3(poll_name, remote_file):
    local_file_name = remote_file + ".tmp"
    boto3.client('s3').download_file(s3bucket, poll_name + '/' + remote_file, local_file_name)
    f = open(local_file_name, "r")
    content = json.loads(f.read())
    f.close()
    os.remove(local_file_name)
    return content

@app.route('/poll/<poll_name>')
def view_poll(poll_name=None):
    poll = read_from_s3(poll_name, 'poll.json')
    return render_template('poll.html', poll=poll, pollName=poll_name)

@app.route('/vote', methods=['POST'])
def vote():
    pollName = request.form['pollName']
    prefs = str(request.form['vote'])
    s3 = boto3.resource('s3')
    s3.Bucket(s3bucket).put_object(Key=pollName + '/vote.' + str(time.time()) + '.dat', Body=prefs)
    return 'Vote received!'
    
@app.route("/count/<poll_name>")
def count(poll_name=None):
    try:
        votes = list()
        s3 = boto3.resource('s3')
        objects = s3.Bucket(s3bucket).objects.all()
        for obj in objects:
            if obj.key.startswith(poll_name + '/' + 'vote'):
                voteFile = obj.key[len(poll_name + '/'):]
                vote = read_from_s3(poll_name, voteFile)
                votes.append(vote)
        return '<html><body>' + counter.build_count_str(votes) + '</body></html>'
    except oops:
        return '<html><body>' + str(oops) + '</body></html>'   

if __name__ == "__main__":
    app.run()
