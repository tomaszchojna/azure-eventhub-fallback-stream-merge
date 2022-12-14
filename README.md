# Flight Stream Simulation

All required Azure infrastructure is scripted in Terraform (terraform/ folder). On `terraform apply` you will be asked for the name of a resource group in which resources should be provisioned.

The simulation is based on multiple docker containers packaged together with docker-compose

`cd docker; docker-compose up`

The frontend is accessible under `localhost:8080`.

## Prerequisites

After running the terraform script, make sure to place the outputs with connection strings in the `docker/.env` file

`AZURE_EVENTHUB_CONNECTION_STRING` and `AZURE_CHECKPOINT_STORAGE_CONTAINER_CONNECTION_STRING` env variables.

## How it works

Roles of the containers from docker-compose file:

- `telemetry_simulator` - simulates a helicopter sharing its location locally, where a device can pull the current position under Redis key `simulation:current_coordinates`

- `low_frequency` and `high_frequency` - scheduled to pull the location from `simulation:current_coordinates` Redis key and publish it to Eventhub stream at specified interval, which is `REFRESH_INTERVAL_SECONDS` environment variable

- `stream_reader` - is connecting with a single connection to Eventhub stream (to avoid reading from eventhub from each websocket connection) and posts the updates to `simulation:eventhub_position` Redis key

- `frontend` - keeps polling changes on `simulation:eventhub_position` Redis key and sends those updates via Websocket to the frontend available under `localhost:8080`

## How to run a simulation

The simulation generates a stream of location between 2 predefined points in `telemetry_simulator` container (check variables START and STOP in app.py).

As it takes some time for the Eventhub stream reader to initialize, wait a bit until logs from `stream_reader` start appearing indicating an established connection.

Open the frontend `localhost:8080` and in a separate terminal window run `docker-compose restart telemetry_simulator`. You can use this command to restart the simulation as well.