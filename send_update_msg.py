from slack import WebClient
from slack.errors import SlackApiError
import os

GET_UPDATE_FROM_SLACK_CHANNEL_NAME = os.getenv(
    'GET_UPDATE_FROM_SLACK_CHANNEL_NAME')
bot_token = os.getenv('API_USER')
client = WebClient(token=bot_token)


# Send message to channel from where updates will be collected
def sendMessage():

    client.chat_postMessage(
        channel=GET_UPDATE_FROM_SLACK_CHANNEL_NAME,
        icon_url="https://files.slack.com/files-pri/T04CAHQGR-F01A3RPBLRF/bot.png?pub_secret=8cce67fe05",
        text="Any update you would like to share ?"
    )


sendMessage()
