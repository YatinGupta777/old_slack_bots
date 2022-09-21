import json
import os
import pickle
from slack import WebClient
from slack.errors import SlackApiError
import requests
from datetime import datetime

SEND_UPDATES_TO_SLACK_CHANNEL_NAME = os.getenv(
    'SEND_UPDATES_TO_SLACK_CHANNEL_NAME')
bot_token = os.getenv('API_USER')
GET_UPDATE_FROM_SLACK_CHANNEL_ID = os.getenv(
    'GET_UPDATE_FROM_SLACK_CHANNEL_ID')
share_update_message = "Any update you would like to share ?"
client = WebClient(token=bot_token)


# Get last 200 msgs of the channel with provided channel id
def get_channel_msgs():
    response = requests.get('https://slack.com/api/conversations.history?token=' +
                            bot_token+'&channel='+GET_UPDATE_FROM_SLACK_CHANNEL_ID+'&limit=200&pretty=1')
    response = json.loads(response.content)
    messages = response['messages']
    return messages


# Get timestamp of the required "any updates" msg
def get_update_msg_ts(messages):
    for i in messages:
        if 'bot_profile' in i:
            if(i['bot_profile']['name'] == "Engineering Bot"):
                if(i['text'] == share_update_message):

                    datetime_of_message = datetime.fromtimestamp(
                        int(int(i['ts'].split('.')[0])))

                    days_difference = (
                        datetime.now() - datetime_of_message).days

                    # Send message only if the timestamp is less than 3 days ago
                    # ( Additional check so that old announcements are not repeated)
                    if(days_difference < 3):
                        return i['ts']

                    return None
    return None


# Get thread replies of msg with the provided timestamp
def get_thread_reply(ts):
    response = requests.get('https://slack.com/api/conversations.replies?token=' +
                            bot_token+'&channel='+GET_UPDATE_FROM_SLACK_CHANNEL_ID+'&ts='+ts+'&pretty=1')
    response = json.loads(response.content)
    replies = []
    for i in response['messages']:
        if 'client_msg_id' in i:
            replies.append(i['text'])
    return replies


# Get updates replies from "any updates" msg
def get_updates():
    messages = get_channel_msgs()
    ts = get_update_msg_ts(messages)
    replies = []

    if(ts):
        replies = get_thread_reply(ts)

    if(replies):
        return replies
    else:
        return []


def send_message_to_slack():

    try:
        update_replies = get_updates()
    except:
        update_replies = []

    if(len(update_replies) > 0):
        update_replies = [
            ':loud_sound: ' + f for f in update_replies]
        update_replies_message = '\n'.join(update_replies)
        try:
            client.chat_postMessage(
                channel=SEND_UPDATES_TO_SLACK_CHANNEL_NAME,
                icon_url="https://files.slack.com/files-pri/T04CAHQGR-F01A3RPBLRF/bot.png?pub_secret=8cce67fe05",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Announcements* !!",
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": update_replies_message
                        },
                        "accessory": {
                            "type": "image",
                            "image_url": "https://files.slack.com/files-pri/T04CAHQGR-F01AW0B412B/announcement.png?pub_secret=ef57bd5ac7",
                            "alt_text": "Growth"
                        }
                    }
                ]
            )
        except SlackApiError as e:
            # You will get a SlackApiError if "ok" is False
            print(e)
            assert e.response["error"]


def main():
    send_message_to_slack()


if __name__ == "__main__":
    main()
