Three scripts :
1. slack_update : that gets the updates with wiki and sends them to channel
2. send_update_msg : that sends "Any update you would like to share ?" msg to a channel
3. read_and_send_updates: this reads updates from channel provided with channel id and sends them to a channel

Commands to run 

```
SLACK_CHANNEL=XXX API_USER=XXX python slack_update.py

GET_UPDATE_FROM_SLACK_CHANNEL_NAME=XXX API_USER=XXX python send_update_msg.py

SEND_UPDATES_TO_SLACK_CHANNEL_NAME=XXX GET_UPDATE_FROM_SLACK_CHANNEL_ID=XXX API_USER=XXXX python read_and_send_updates.py

```

