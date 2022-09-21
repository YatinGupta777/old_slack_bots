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
client = WebClient(token=bot_token)

def send_message_to_slack():
    try:
        client.chat_postMessage(
            channel=SEND_UPDATES_TO_SLACK_CHANNEL_NAME,
            icon_url="https://files.slack.com/files-pri/T04CAHQGR-F01A3RPBLRF/bot.png?pub_secret=8cce67fe05",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Hello Human <@prasanna>",
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "I have been trained to call you sensei.\n Thank you for giving me life, I guess this is goodbye for now but if I run into any error please come to my rescue, cant rely on these other noob humans in this group. \n Jokes aside, Thank you so much prasanna for helping us. We learnt more from you working on a side-project than our professors ( 4 years combined ).\n Thank you for creating wiki, coming up with innovative ideas and taking out time for us from your very busy schedule.\n Any last '2 Cents' for us? :sadok: "
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": "https://files.slack.com/files-pri/T04CAHQGR-F01J5JX6CBT/captain.jpg?pub_secret=1e9c8dd752",
                        "alt_text": "O Captain My Captain"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Rule of thumb - Stuck somewhere? Read them logs"
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": "https://avatars.slack-edge.com/2015-07-06/7262503766_3b26ee6c54d4726922b1_original.jpg",
                        "alt_text": "O Captain My Captain"
                    }
                }
            ]
        )
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        print(e)
        assert e.response["error"]

send_message_to_slack()