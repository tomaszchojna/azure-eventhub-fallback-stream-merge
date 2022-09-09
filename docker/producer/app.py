import asyncio
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData
import os
import aioredis
import json
import logging
import sys
import uuid


logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


CONNECTION_STRING = os.getenv('AZURE_EVENTHUB_CONNECTION_STRING')
EVENTHUB_NAME = os.getenv('AZURE_EVENTHUB_NAME')
REFRESH_INTERVAL_SECONDS = float(os.getenv('REFRESH_INTERVAL_SECONDS'))
SIMULATION_TYPE = os.getenv('SIMULATION_TYPE')


async def run():
    redis = await aioredis.from_url(os.getenv('REDIS_URL'))

    producer = EventHubProducerClient.from_connection_string(
        conn_str=CONNECTION_STRING,
        eventhub_name=EVENTHUB_NAME
    )


    async with producer:
        last_message = ''

        while True:
            active = await redis.get(f'simulation:{SIMULATION_TYPE}:active')
            logger.info(f'Checking activity flag={active} for {SIMULATION_TYPE}')
            
            if active and (active.decode('utf-8') == '1'):
                current_coordinates = (await redis.get(f'simulation:current_coordinates')).decode('utf-8')

                logger.info(f'Comparing payloads {current_coordinates} vs {last_message}')
                if current_coordinates != last_message:
                    payload = {
                        'coordinates': current_coordinates,
                        'stream': SIMULATION_TYPE,
                        'uuid': str(uuid.uuid4())
                    }

                    logger.info(
                        f'Publishing to EventHub message={payload}'
                    )

                    event_data_batch = await producer.create_batch()
                    event_data_batch.add(EventData(json.dumps(payload)))

                    await producer.send_batch(event_data_batch)

                    last_message = current_coordinates

            await asyncio.sleep(REFRESH_INTERVAL_SECONDS)

loop = asyncio.get_event_loop()
loop.run_until_complete(run())
