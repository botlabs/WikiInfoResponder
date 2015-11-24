import praw
import re
import requests
from time import sleep

# Account settings (private)
USERNAME = ''
PASSWORD = ''

# OAuth settings (private)
CLIENT_ID = ''
CLIENT_SECRET = ''
REDIRECT_URI = ''

# Settings
USER_AGENT = "/r/Legodimensions Info Respond Bot"
SUBREDDIT = "Legodimensions"

# The tag found in comments which the bot will reply to
REGEX_TAG = "\[\[([^\]]+)\]\]" # matches things like [[this]]

# A regex which extracts (title) and (body) data from some markdown syntax
MD_REGEX = "##\s*(.+?)[\r\n]+(.+?)(?=##)"

RESPONSE_TEMPLATE = u"#{title}\n\n{body}\n\n"
RESPONSE_SUFFIX = u"\n\n----------\n\n I am a bot."
PROCESSED_LOG = "processed.txt"
AUTH_TOKENS = ["identity", "submit", "read"]

def get_access_token():
    response = requests.post("https://www.reddit.com/api/v1/access_token",
      # client id and client secret are obtained via your reddit account
      auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
      # provide your reddit user id and password
      data = {"grant_type": "password", "username": USERNAME, "password": PASSWORD},
      # you MUST provide custom User-Agent header in the request to play nicely with Reddit API guidelines
      headers = {"User-Agent": USER_AGENT})
    response = dict(response.json())
    return response["access_token"]

def get_praw():
    r = praw.Reddit(USER_AGENT)
    r.set_oauth_app_info(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
    r.set_access_credentials(set(AUTH_TOKENS), get_access_token())
    return r

def main(r):
    # Retrieve wiki data
    wiki_pieces = r.get_wiki_page(SUBREDDIT,"pieces")
    wiki_abilities = r.get_wiki_page(SUBREDDIT,"abilities")

    pieces = dict((x.strip().lower(), y.strip()) for x,y in re.findall(MD_REGEX, wiki_pieces.content_md, re.M | re.S))
    abilities = dict((x.strip().lower(), y.strip()) for x,y in re.findall(MD_REGEX, wiki_abilities.content_md, re.M | re.S))

    # Main loop
    sub = r.get_subreddit(SUBREDDIT)

    open(PROCESSED_LOG, 'a').close()
    with open(PROCESSED_LOG, 'r') as f:
        processed = f.read().split("\n")


    while True:
        try:
            comments = sub.get_comments(limit=None)     
            for comment in comments:
                if comment.id not in processed:
                    processed.append(comment.id)
                    matches = re.findall(REGEX_TAG, comment.body)
                    if len(matches) > 0:
                        response = ""
                        for match in matches:
                            index = match.lower()
                            if index in pieces:
                                response += RESPONSE_TEMPLATE.format(title=index.title(), body=pieces[index])
                            if index in abilities:
                                response += RESPONSE_TEMPLATE.format(title=index.title(), body=abilities[index])
                        if len(response) > 0:
                            comment.reply(response + RESPONSE_SUFFIX)

            with open(PROCESSED_LOG, 'w') as f:
                f.write(''.join(id+"\n" for id in processed))
            sleep(30)
        except OAuthInvalidToken:
            r = get_praw()

if __name__ == "__main__":
    main(get_praw())
