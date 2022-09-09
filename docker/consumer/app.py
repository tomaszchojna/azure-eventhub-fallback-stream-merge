import asyncio
from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore
from azure.eventhub import EventData
import os
import aioredis
import json
import logging
import sys

logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.ERROR)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


CONNECTION_STRING = os.getenv('AZURE_EVENTHUB_CONNECTION_STRING')
EVENTHUB_NAME = os.getenv('AZURE_EVENTHUB_NAME')

STORAGE_CONTAINER_CONNECTION_STRING = os.getenv('AZURE_CHECKPOINT_STORAGE_CONTAINER_CONNECTION_STRING')
BLOB_CONTAINER_NAME = os.getenv('AZURE_CHECKPOINT_STORAGE_BLOB_NAME')
EVENTHUB_CONSUMER_GROUP = os.getenv('AZURE_EVENTHUB_CONSUMER_GROUP')


async def on_event(partition_context, event):
    redis = await aioredis.from_url(os.getenv('REDIS_URL'))
    
    body = event.body_as_str(encoding='UTF-8')

    try:
        logger.info(f'Reading from eventhub_name={EVENTHUB_NAME}, body: {body}')
        await redis.set('simulation:eventhub_position', body)
    except:
        logger.exception(f'Failed loading body from eventhub stream: {body}')

async def run():
    checkpoint_store = BlobCheckpointStore.from_connection_string(
        STORAGE_CONTAINER_CONNECTION_STRING,
        BLOB_CONTAINER_NAME
    )

    client = EventHubConsumerClient.from_connection_string(
        CONNECTION_STRING,
        consumer_group=EVENTHUB_CONSUMER_GROUP,
        eventhub_name=EVENTHUB_NAME,
        checkpoint_store=checkpoint_store
    )

    async with client:
        await client.receive(
            on_event=on_event,
            starting_position="-1"
        )


loop = asyncio.get_event_loop()
loop.run_until_complete(run())
