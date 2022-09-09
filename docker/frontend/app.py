from aiohttp import web
import aiohttp_jinja2
import jinja2
from pathlib import Path
from dataclasses import dataclass
import aioredis
import os
import asyncio
import logging
import sys
import json
import aiohttp

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


here = Path(__file__).resolve().parent


@aiohttp_jinja2.template('index.html')
async def handle(request):
    redis = await aioredis.from_url(os.getenv('REDIS_URL'))
    
    start_coordinates = await redis.get('simulation:start_coordinates')
    stop_coordinates = await redis.get('simulation:end_coordinates')

    return {
        "start": start_coordinates.decode('utf-8'),
        "stop": stop_coordinates.decode('utf-8')
    }


async def listen_to_location_updates(ws):
    logger.info('Listening to redis updates')

    redis = await aioredis.from_url(os.getenv('REDIS_URL'))

    last_location = ''    

    while True:
        payload = await redis.get('simulation:eventhub_position')
        completed = (await redis.get('simulation:completed')).decode('utf-8')

        if (payload != last_location) and completed != '1':
            try:
                await ws.send_str(payload.decode('utf-8'))
            except:
                logger.exception('Error publishing message')

        last_location = payload

        await asyncio.sleep(0.1)


async def handle_client_messages(ws):
    redis = await aioredis.from_url(os.getenv('REDIS_URL'))

    async for msg in ws:
        logger.info(f'Received message: {msg}')

        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            elif msg.data == 'low_frequency:start':
                await redis.set('simulation:low_frequency:active', 1)
            elif msg.data == 'low_frequency:stop':
                await redis.set('simulation:low_frequency:active', 0)
            elif msg.data == 'high_frequency:start':
                await redis.set('simulation:high_frequency:active', 1)
            elif msg.data == 'high_frequency:stop':
                await redis.set('simulation:high_frequency:active', 0)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logger.error(f'ws connection closed with exception {ws.exception()}')


async def websocket_handler(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    await asyncio.gather(
        handle_client_messages(ws),
        listen_to_location_updates(ws)
    )

    logger.info('websocket connection closed')

    return ws


app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(str(here)))
app.add_routes([
    web.get('/', handle),
    web.get('/ws', websocket_handler)
])

if __name__ == '__main__':
    web.run_app(app)
