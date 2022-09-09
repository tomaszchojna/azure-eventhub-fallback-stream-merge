import aioredis
import asyncio
from dataclasses import dataclass
import os
import logging
import sys
import copy
import json
import random

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@dataclass
class Point:
    lat: float
    lng: float

    def __str__(self):
        return f'{self.lng},{self.lat}'


START = Point(lat=47.34596992410861, lng=8.456555957031252)
STOP = Point(lat=47.41083243873547, lng=8.627702349853518)

DELTA_CHANGE = 0.001

async def simulate_flight():
    logger.info('Starting the location sending')

    redis = await aioredis.from_url(os.getenv('REDIS_URL'))
    
    await redis.set('simulation:completed', str(0))
    await redis.delete('simulation:current_coordinates')
    await redis.delete('simulation:eventhub_position')
    await redis.set('simulation:low_frequency:active', str(1))
    await redis.set('simulation:high_frequency:active', str(1))

    await redis.set('simulation:start_coordinates', str(START))
    await redis.set('simulation:end_coordinates', str(STOP))

    current_point = copy.deepcopy(START)

    while (current_point.lat < STOP.lat) or (current_point.lng < STOP.lng):
        current_point = Point(
            lat=min(current_point.lat + DELTA_CHANGE, STOP.lat),
            lng=min(current_point.lng + DELTA_CHANGE, STOP.lng)
        )

        await redis.set('simulation:current_coordinates', str(current_point))
    
        await asyncio.sleep(0.5)

    await redis.set('simulation:completed', str(1))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(simulate_flight())

    
