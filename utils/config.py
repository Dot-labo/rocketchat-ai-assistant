import os
from dotenv import load_dotenv

class RocketChatConfig:
    def __init__(self, url, username, password, port, prompt):
        self.socket_url = f'wss://{url}/websocket'
        self.username = username
        self.password = password
        self.port = port
        self.prompt = prompt

class Config:
    def __init__(self, path="./.env"):
        load_dotenv(path)
        self.socket_url = f'wss://{os.getenv("URL")}/websocket'
        self.username = os.getenv("NAME")
        self.password = os.getenv("PASSWORD")
        self.port = os.getenv("PORT")
        self.prompt = os.getenv("AI_PROMPT")

    @property
    def rocket_chat_config(self):
        return RocketChatConfig(
            url=self.socket_url,
            username=self.username,
            password=self.password,
            port=self.port,
            prompt=self.prompt
        )