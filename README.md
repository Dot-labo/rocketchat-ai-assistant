# Integrate AI for your rocket.chat server!

Enhance your Rocket.Chat server with AI capabilities by integrating the latest OpenAI ChatGPT-4 Turbo model for real-time messaging.
This integration does not require any installations or modifications to your Rocket.Chat server itself, making it easy to deploy.
All you need are two steps: 1. create an account for the bot on Rocket.Chat, and 2. Download this repository to your PC and run the server program.
Currently, the system supports only the OpenAI ChatGPT-4 Turbo model, but we are planning to expand support to include a variety of models in the future to accommodate a broader range of functionalities and use cases.

## Requirements
- python 3.9+  
- poetry  
- rocket.chat server version 6.x

## Setup Instructions
### 1. clone the repository
```
git clone --recurse-submodules https://github.com/Dot-labo/rocketchat-ai-assistant
```
   
### 2. Install dependencies
Navigate to the cloned directory and install the required dependencies using Poetry:
```
poetry install
```

### 3. Set Up the Bot Account
Set up an account on your Rocket.Chat server to be used as a bot.
Ensure that the bot’s username and password match those specified in the .env file created in the next step. The bot user must join the desired channels before running the server.
   
### 4. Configure Environment
Ensure to place a .env file at the root of your project directory with the following contents.
Remember to replace the placeholders with your actual data:
```
URL=xxx.com (don't include http:// or https://)
NAME=bot
PASSWORD=password
PORT=8000
OPENAI_API_KEY=sk-xxxxx
AI_PROMPT="You are ..."
```

### 5. Run the server
```
poetry shell
uvicorn main:app --port 8000
````

## Additional Information
- Ensure that your network settings allow traffic on the specified port (default: 8000).
- Occasionally, typing events fail to generate properly. The specific cause is unclear, but alleviating the API rate_limit settings in the management console of rocket.chat sometimes leads to improvement.
