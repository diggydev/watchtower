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
    votes = list()
    s3 = boto3.resource('s3')
    objects = s3.Bucket(s3bucket).objects.all()
    for obj in objects:
        if obj.key.startswith(poll_name + '/' + 'vote'):
            voteFile = obj.key[len(poll_name + '/'):]
            print(voteFile)
            vote = read_from_s3(poll_name, obj.key[len(poll_name + '/'):])
            print(vote)
            votes.append(vote)
    print(votes)

def count1(votes):
    quota = int(len(votes)/2) + 1
    print("Quota " + str(quota))

    currRoundVotes = dict()

    for vote in votes:
        for item in vote.items():
            print(item[0])
            print(item[1])
            print("**")
        


if __name__ == "__main__":
    #app.run()
    #view_poll("cbc1")
    #print(read_from_s3("cbc_april", "poll.json"))
#    count1([{'book1': '3', 'book2': '2', 'book3': '1'}, {'book1': '1', 'book2': '2', 'book3': '3'}, {'book1': '3', 'book2': '2', 'book3': '1'}])
    count1([{'X': '1', 'L': '2', 'C': '3', 'A': '4'}, {'L': '1', 'X': '2', 'C': '3', 'A': '4'}, {'C': '1', 'X': '2', 'L': '3', 'A': '4'}, {'L': '1', 'C': '2', 'A': '3', 'X': '4'}, {'C': '1', 'A': '2', 'L': '3', 'X': '4'}, {'A': '1', 'L': '2', 'C': '3', 'X': '4'}, {'X': '1', 'L': '2', 'A': '3', 'C': '4'}, {'L': '1', 'C': '2', 'X': '3', 'A': '4'}, {'A': '1', 'L': '2', 'X': '3', 'C': '4'}, {'L': '1', 'C': '2', 'A': '3', 'X': '4'}, {'C': '1', 'X': '2', 'A': '3', 'L': '4'}])



