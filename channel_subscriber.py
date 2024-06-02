import os
import json
import asyncio
import aiohttp
import random
from dotenv import load_dotenv
from openai import OpenAI
from rocketchat_async import RocketChat

from utils.http_utils import fetch_data
from utils.message_utils import send_message_with_retry, send_typing_event_periodically
from utils.config import Config

class ChannelSubscriber:
    def __init__(self, address, username, password, channel_id, channel_type, say_hello=False):
        #Setup GPT assistant and thread 
        self.config = Config("./.env")
        self.channel_id = channel_id
        self.channel_type = channel_type #c: channel, p: private channel, d: direct message
        self.say_hello = say_hello
        self.rc = RocketChat()
        self.client = OpenAI(organization=self.config.openai_organization) if self.config.openai_organization else OpenAI()
        self.thread_mapping = {}
        self.subscription_id = None
        self.assistant = self.client.beta.assistants.create(
            name = "Rocket chat assistant",
            description = "You are talking to an AI assistant chat bot.",
            model = "gpt-4-1106-preview",
            instructions = self.config.prompt,
            tools=[{"type": "retrieval"}],
            file_ids=[]
        )

    def get_openai_thread_id(self, rocket_chat_thread_id):
        openai_thread_id = self.thread_mapping.get(rocket_chat_thread_id, None)
        if openai_thread_id is None:
            new_thread = self.client.beta.threads.create()
            openai_thread_id = new_thread.id
            print("openai_thread_id:", openai_thread_id)
            self.thread_mapping[rocket_chat_thread_id] = openai_thread_id
        print("openai_thread_id:", openai_thread_id)
        return openai_thread_id

    def subscribe_callback(self, *args):
        asyncio.create_task(self.process_incoming_messages(*args))

    async def process_incoming_messages(self, channel_id, sender_id, msg_id, thread_id, msg, qualifier, unread, re_received):
        print("=== DEBUG: process_incoming_messages ===")
        print(f"channel_id: {channel_id}, sender_id: {sender_id}, msg_id: {msg_id}, thread_id: {thread_id}, msg: {msg}, qualifier: {qualifier}, unread: {unread}, re_received: {re_received}\n")
        """
        Handle incoming messages and perform actions based on the message context.
        - Unsubscribes if no longer member of the channel.
        - Ends if the message is re-received.
        - Creates a new thread for new messages with mentions.
        - Replies within the existing thread for threaded messages with mentions.
        """
        tmp_rc = RocketChat() #self.rc is not working here
        config = Config("./.env")
        await tmp_rc.start(config.socket_url, config.username, config.password)
        tmp_channel_list=[]
        for channel_id, channel_type in await tmp_rc.get_channels():
            tmp_channel_list.append(channel_id)
        if not self.channel_id in tmp_channel_list:
            await self.rc.unsubscribe(subscription_id=self.subscription_id)
            return

        if re_received:
            return

        if "@" + self.config.username in msg:
            await self.handle_message_with_mention(channel_id, sender_id, msg_id, thread_id, msg)

    async def handle_message_with_mention(self, channel_id, sender_id, msg_id, thread_id, msg):
        """
        Handles messages that contain a mention of the assistant.
        """
        ai_thread_id = self.get_openai_thread_id(thread_id if thread_id else msg_id)
        payload = {
            "assistant_id": str(self.assistant.id),
            "ai_thread_id": str(ai_thread_id),
            "user_name": "usr1",  # TODO: Retrieve actual username using sender_id
            "input_message": msg
        }
        typing_task = asyncio.create_task(send_typing_event_periodically(self.rc, channel_id, thread_id))
        try:
            response = await fetch_data(f"http://localhost:{self.config.port}/gpt_response", payload)
            task = asyncio.create_task(send_message_with_retry(self.rc, response, channel_id, thread_id or msg_id))
            await task
        finally:
            typing_task.cancel()
            await typing_task


    async def up(self):
        while True:
            try:
                await self.rc.start(self.config.socket_url, self.config.username, self.config.password)
                self.subscription_id = await self.rc.subscribe_to_channel_messages(self.channel_id, self.subscribe_callback)
                if self.say_hello == True:
                    await self.rc.send_message(text=f"*Hi. I'm ready.*", channel_id=self.channel_id, thread_id=None)
                await self.rc.run_forever()

            except Exception as e:
                print(f'Error: {e}. Reconnecting...')
                await asyncio.sleep(random.uniform(4, 8)) 

if __name__ == "__main__":
    load_dotenv("./.env")
    url = os.getenv("URL")
    username = os.getenv("NAME")
    password = os.getenv("PASSWORD")
    prompt = os.getenv("AI_PROMPT")
    channel_id = "GENERAL"
    print("url:", url)
    print("username:", username)
    print("password:", password)
    cs = ChannelSubscriber(url, username, password, channel_id)
    asyncio.run(cs.up())