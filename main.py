import time
from pydantic import BaseModel
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi import BackgroundTasks
import os
from openai import OpenAI
import asyncio
from channel_subscriber import ChannelSubscriber
from rocketchat_async import RocketChat

from utils.config import Config

class ResponseMessageModel(BaseModel):
    assistant_id: str
    ai_thread_id: str
    user_name: str
    input_message: str

global client
global thread_id
global assistant_id

app = FastAPI()
global cs_dict
cs_dict = {} # {channel_id: ChannelSubscriber}

async def periodic_cs_management(cs_dict, interval=5):
    while True:
        config = Config("./.env")
        rc = RocketChat()
        try:
            user_joining_channel_list = []
            user_joining_channel_type = []
            await rc.start(config.socket_url, config.username, config.password)
            await asyncio.sleep(interval)  # 非同期的に待機
            for channel_id, channel_type in await rc.get_channels():
                print(channel_id, channel_type)
                user_joining_channel_list.append(channel_id)
                user_joining_channel_type.append(channel_type)

            for channel_id in list(cs_dict.keys()):
                if channel_id not in user_joining_channel_list:
                    cs = cs_dict[channel_id]
                    await cs.down()
                    del cs_dict[channel_id]
                else:
                    pass
            
            for channel_id, channel_type in zip(user_joining_channel_list, user_joining_channel_type):
                if channel_id not in cs_dict:
                    if channel_type == "d":
                        say_hello = True
                    else:
                        say_hello = False
                    cs = ChannelSubscriber(config.socket_url, config.username, config.password, channel_id, channel_type, say_hello=say_hello)
                    asyncio.create_task(cs.up())
                    print("DEBUG: cs.up() is called")
                    cs_dict[channel_id] = cs
                else:
                    pass
                
        except Exception as e:
            print(f"Error in periodic_cs_management: {e}")
        finally:
            print("===")



@app.on_event("startup")
async def startup_event():
    global cs_dict
    asyncio.create_task(periodic_cs_management(cs_dict=cs_dict, interval=5))

@app.on_event("shutdown")
async def shutdown_event():
    config = Config("./.env")
    rc = RocketChat()
    await rc.start(config.socket_url, config.username, config.password)
    for channel_id, channel_type in await rc.get_channels():
        print(channel_id, channel_type)
        await rc.send_message(text=f"*Bye.*", channel_id=channel_id, thread_id=None)

@app.post("/gpt_response")
async def gpt_response(input: ResponseMessageModel):
    config = Config("./.env")
    print("#DEBUG in gpt_response(FastAPI)")
    input_message = input.input_message
    user = input.user_name
    client = OpenAI(organization=config.openai_organization) if config.openai_organization else OpenAI()
    assistant_id = input.assistant_id
    ai_thread_id = input.ai_thread_id

    print("user:", user)
    print("input_message:", input_message)
    print("client:", client)
    print("ai_assistant_id:", assistant_id)
    print("ai_thread_id:", ai_thread_id)

    input_message = f"@{user} : {input_message}"
    print("The message to be processed: ", input_message)

    try:
        message = client.beta.threads.messages.create(
            thread_id=ai_thread_id,
            role="user",
            content=input_message,
        )
        run = client.beta.threads.runs.create(
            thread_id = ai_thread_id,
            assistant_id = assistant_id
        )
        print("run_id is :",run.id)

        while True:
            run_retrieve = client.beta.threads.runs.retrieve(
                thread_id = ai_thread_id,
                run_id = run.id,
            )
            if run_retrieve.status == "completed":
                break
            else:
                print(".", end="", flush=True)
                await asyncio.sleep(3)
        messages = client.beta.threads.messages.list(
            thread_id=ai_thread_id
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    try:
        return_json = {"response": messages.data[0].content[0].text.value}
        return(messages.data[0].content[0].text.value)
    except:
        return("No response from the AI")