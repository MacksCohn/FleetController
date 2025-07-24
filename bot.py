import os
from dotenv import load_dotenv

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import boto3


class MainMessage:
    ts = None
    channel = None
    text = None
    messageDict = {
        'Default': '*Fleet Controls*' + '\n>Please double click buttons.',
        'Start': '>Please double click buttons.\n>Starting Fleet',
        'Stop': '>Please double click buttons.\n>Stopping Fleet',
    }


startEmoji = ':white_check_mark:'
start = 'white_check_mark'
startCheckedEmoji = ':ballot_box_with_check:'
startChecked = 'ballot_box_with_check'
stopEmoji = ':octagonal_sign:'
stop = 'octagonal_sign'
refresh = 'arrows_counterclockwise'
refreshEmoji = ':arrows_counterclockwise:'

fleetName = 'flir-demo'
mainMessage = MainMessage()


def main():
    load_dotenv()
    GetFleetStatus(fleetName)

    SECRET = os.getenv('SECRET')
    TOKEN = os.getenv('TOKEN')
    APP_TOKEN = os.getenv('APP')
    CHANNEL_NAME = 'flir-fleet-controller'
    CHANNEL_ID = 'C096JLGB27R'

    app = App(token=TOKEN, signing_secret=SECRET)
    client = WebClient(token=TOKEN)

    ClearOldMessages(client, CHANNEL_ID)
    mainMessage.ts = SendMessage(client, CHANNEL_NAME, mainMessage.messageDict['Default'])
    AddReactionsToMessage(
        client,
        CHANNEL_ID,
        mainMessage.ts,
        [start, stop, refresh]
    )

    @app.event('reaction_added')
    def _OnReactionAdded(event, say):
        if event['reaction'] == start:
            mainMessage.ts = EditMessageWithReactions(
                client=client,
                id=CHANNEL_ID,
                timestamp=mainMessage.ts,
                state='Start',
                reactions=[startChecked, stop, refresh],
            )
            StartFleet(fleetName)
            SetStatusInMessage(client, CHANNEL_ID, mainMessage.ts, 'Start')
        if event['reaction'] == stop:
            mainMessage.ts = EditMessageWithReactions(
                client=client,
                id=CHANNEL_ID,
                timestamp=mainMessage.ts,
                state='Stop',
                reactions=[start, stop, refresh],
            )
            StopFleet(fleetName)
            SetStatusInMessage(client, CHANNEL_ID, mainMessage.ts, 'Stop')
        if event['reaction'] == refresh:
            SetStatusInMessage(
                client,
                CHANNEL_ID,
                mainMessage.ts,
                'Default',
            )

    SetStatusInMessage(client, CHANNEL_ID, mainMessage.ts, 'Default')
    handler = SocketModeHandler(app, APP_TOKEN)
    handler.start()


def EditMessageWithReactions(client, id, state, timestamp, reactions):
    client.chat_update(
        channel=id,
        ts=timestamp,
        text=mainMessage.messageDict[state],
    )
    AddReactionsToMessage(
       client,
       id,
       timestamp,
       reactions,
    )
    return timestamp


def AddReactionsToMessage(client, CHANNEL_ID, ts, reactions):
    try:
        RemoveCurrentReactions(client, CHANNEL_ID, ts)
        for reaction in reactions:
            client.reactions_add(
                channel=CHANNEL_ID,
                timestamp=ts,
                name=reaction,
            )
    except Exception as e:
        print(f'Reactions error: {e}')


def RemoveCurrentReactions(client: WebClient, channel, ts):
    reactions = client.reactions_get(
        channel=channel,
        timestamp=ts,
    )
    if 'reactions' not in reactions['message']:
        return

    for reaction in reactions['message']['reactions']:
        client.reactions_remove(
            channel=channel,
            timestamp=ts,
            name=reaction['name']
        )


def ClearOldMessages(client, id):
    try:
        messages = client.conversations_history(channel=id, limit=100)
        for message in messages['messages']:
            try:
                client.chat_delete(
                    channel=id,
                    ts=message['ts']
                )
            finally:
                continue
    except Exception as e:
        print(f'messages not found {e}')


def SendMessage(client, name, message):
    try:
        response = client.chat_postMessage(
            channel=name,
            text=message,
        )
        return response['ts']
    except SlackApiError as e:
        print(e.response)
        return None


def SetStatusInMessage(client: WebClient, id, timestamp, state: str):
    try:
        previous: str = mainMessage.messageDict[state]
        if '```' in previous:
            previous = previous[:previous.index('```')-1]
        client.chat_update(
            channel=id,
            ts=timestamp,
            text=previous + '\n```\n' + GetFleetStatus(fleetName) + '```',
        )
    except Exception as e:
        print(f'error in SetStatusInMessage {e}')


def GetLastMessageTimestamp(client: WebClient, channel):
    try:
        response = client.conversations_history(channel=channel)
        return response['messages'][0]['ts']
    except Exception as e:
        print(f'error in GetLastMessageTimestamp {e}')


def GetFleetStatus(name):
    try:
        appStreamClient = boto3.client('appstream')
        response = appStreamClient.describe_fleets(
            Names=[name],
        )
        return response['Fleets'][0]['State']
    except Exception as e:
        print(f'Fleet status error: {name}:{e}')
        return None


def StartFleet(name):
    try:
        appStreamClient = boto3.client('appstream')
        response = appStreamClient.start_fleet(
            Name=name,
        )
        print(f'Fleet "{name}" started successfully')
        return response
    except Exception as e:
        print(f'Fleet start error: {name}:{e}')
        return None


def StopFleet(name):
    try:
        appStreamClient = boto3.client('appstream')
        response = appStreamClient.stop_fleet(
            Name=name,
        )
        print(f'Fleet "{name}" stopped successfully')
        return response
    except Exception as e:
        print(f'Fleet start error: {name}:{e}')
        return None


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\nBot taken offline.')
