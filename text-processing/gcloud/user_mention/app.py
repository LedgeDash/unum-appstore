import re

user_mention_pattern = re.compile(r"@[a-zA-Z0-9]+")

def lambda_handler(event, context):
    user_mentions = user_mention_pattern.findall(event)
    user_mentions = [u[1:] for u in user_mentions if u[0] == "@"]

    return user_mentions
