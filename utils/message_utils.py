import random
import asyncio
from websockets.exceptions import ConnectionClosedOK

async def send_message_with_retry(rc, response, channel_id, thread_id, max_retries=10):
    retries = 0
    while retries < max_retries:
        try:
            print(f"Attempting to send message {retries + 1}/{max_retries}")
            await rc.send_message(text=response, channel_id=channel_id, thread_id=thread_id)
            return
        except ConnectionClosedOK:
            retries += 1
            if retries >= max_retries:
                print(" * Maximum retry attempts reached. Message sending failed. * ")
                return
            await asyncio.sleep(random.uniform(5, 12))
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            return

async def send_typing_event_periodically(rc, channel_id, thread_id=None, interval=3):
    while True:
        print("Sending typing event...")
        try:
            await rc.send_typing_event(channel_id, thread_id)
            await asyncio.sleep(interval)
        except ConnectionClosedOK:
            return
        except Exception as e:
            print(f"Error in 'send_typing_event_periodically': {e}")
            return