# Requires the following env variables to be set:
# AWS_ACCESS_KEY_ID
# AWS_SECRET_ACCESS_KEY
# AWS_S3_BUCKET
# PORT

from flask import Flask
from flask import request
import boto3
import json
import time
import os
import sys

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
    return '<html><body>' + build_count_str(votes) + '</body></html>'

def get_options(votes):
    options = set()
    for vote in votes:
        options.update(vote.keys())
    return options

def find_eliminated(counted_votes):
    min_count = sys.maxsize
    for count in counted_votes.values():
        if count < min_count:
            min_count = count
    eliminated = set()
    for count in counted_votes.items():
        if count[1] == min_count:
            eliminated.add(count[0])
    return eliminated

def remove_eliminated(votes, eliminated):
    for eliminated_option in eliminated:
        for vote in votes:
            del vote[eliminated_option]

def check_meets_quota(counted_votes, quota):
    for count in counted_votes.values():
        if count >= quota:
            return True
    return False

def find_highest_preference(vote, num_options):
    highest_pref_value = num_options
    for item in vote.items():
        if int(item[1]) <= highest_pref_value:
            highest_pref_value = int(item[1])
            highest_pref = item[0]
    return highest_pref

def reset_counted_votes(options):
    counted_votes = dict()
    for option in options:
        counted_votes[option] = 0
    return counted_votes

def build_count_str(votes):
    options = get_options(votes)
    num_options = len(options)
    page = "The options are " + str(options) + '<br>'
    page += "The votes are " + str(votes) + '<br>'
    page += "The number of votes is " + str(len(votes)) + '<br>'
    quota = int(len(votes)/2) + 1
    page += "The quota is " + str(quota) + '<br>'

    while(True):
        counted_votes = reset_counted_votes(options)

        #first round
        for vote in votes:
            counted_votes[find_highest_preference(vote, num_options)] += 1
        page += "The current count is " + str(counted_votes) + '<br>'
        if check_meets_quota(counted_votes, quota):
            page += "Quota met" + '<br>'
            return page

        eliminated = find_eliminated(counted_votes)
        page += "The eliminated options are " + str(eliminated) + '<br>'

        remove_eliminated(votes, eliminated)

        if len(votes[0]) <= 1:
            page += "All done" + '<br>'
            return page
    
        page += "The votes are " + str(votes) + '<br>'    

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ['PORT'])


