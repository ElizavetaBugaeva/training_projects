"""
This script gets reddits from the reddit api 
and serves as the first step of the dockerized pipeline.

TO DO -add Mongodb connection with pymongo and insert reddits into Mongodb -> Thursday
"""
import requests
from requests.auth import HTTPBasicAuth
import sys
from config import tokens  # This is from our config.py containing our credentials.
import datetime
import pymongo

client = pymongo.MongoClient(host="mongodb", port=27017)
db = client.reddit

#sys.stdout.reconfigure(encoding='utf-8') # Useful for windows user

## PREPARE AUTHENTIFICATION INFORMATION ##
## FOR REQUESTING A TEMPORARY ACCESS TOKEN ##

basic_auth = HTTPBasicAuth(
    username=tokens['client_id'], # the client id
    password=tokens['secret']  # the secret
)


GRANT_INFORMATION = dict(
    grant_type="password",
    username=tokens['username'], # REDDIT USERNAME
    password=tokens['password'] # REDDIT PASSWORD
)

headers = {
    'User-Agent': 'TestAppforDocker'
}


### POST REQUEST FOR ACCESS TOKEN

POST_URL = "https://www.reddit.com/api/v1/access_token"

access_post_response = requests.post(
    url=POST_URL,
    headers=headers,
    data=GRANT_INFORMATION,
    auth = basic_auth
).json()

# Print the Bearer Token sent by the API
print(access_post_response)

### ADDING TO HEADERS THE Authorization KEY

headers['Authorization'] = access_post_response['token_type'] + ' ' + \
                           access_post_response['access_token']

print(headers)

## Send a get request to download the latest (new) subreddits using the new headers.

topic = 'Berlin'
URL = f"https://oauth.reddit.com/r/{topic}/new"  # You could also select ".../hot" to fetch the most popular posts.

response = requests.get(
    url=URL,
    headers=headers  # this request would not work without the access token 
).json()

# We have what we want but would need to read the doc about 
# the structure and content of 'response' (https://www.reddit.com/dev/api/).
# To shorten it, I have already done so.
# response is a dict with these keys
print(response.keys())
print(type(response['data']))
print(response['data'].keys())
print(type(response['data']['children']))

full_response = response['data']['children'] #
print(type(full_response[0]))

# Go through the full response and define a mongo_input dict
# see full_response[0]['data'].keys() for a list of possibilities

for post in full_response:
    _id = post['data']['id']
    subreddit_id = post['data']['subreddit_id']
    time = post['data']['created_utc']  # time in seconds since 1970
    time = datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
    subreddit = post['data']['subreddit']  # the above defined 'topic'
    title = post['data']['title']
    text = post['data']['selftext']  # the actual content

    # Check if the document already exists in the collection
    existing_doc = db.posts.find_one({'_id': _id})
    if existing_doc:
        # Update the existing document
        db.posts.update_one({'_id': _id}, {'$set': {'sub_id': subreddit_id, 'date': time, 'text': text}})
    else:
        # Insert a new document
        mongo_input = {'_id': _id, 'sub_id': subreddit_id, 'date': time, 'text': text}
        #print(mongo_input)
        db.posts.insert_one(mongo_input)
 


