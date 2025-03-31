# InfluxDB 3 Custom Data Replication Plugin

This plugin replicates **any/all data** written to an InfluxDB 3 Core/Enterprise instance to a remote InfluxDB 3 bucket (e.g Cloud Serverless Instance). It features durable queuing, compression, validation, downsampling, and table filtering, and is source-agnostic, working with Telegraf, custom scripts, or any client.

## Prerequisites
- **InfluxDB v3 Core**: Public beta (March 29, 2025).
- **InfluxDB Cloud Account**: InfluxDB 3 Account information where you want to replicate data e.g. Cloud Serverless URL, API Token with write access for the given bucket/database where data needs to be replicated.
- **Telegraf**: For collecting system metrics (optional). Anytime, however data gets written to InfluxDB 3 Core/Enterprise, this plugin will come into action.
- **Python**: 3.7+ 

## Files
- `data-replicator.py`: Data replication plugin code
- `telegraf.conf`: Example Telegraf config for collecting and wrting system metrics.

## Features

- Custom Data Replication: Replicate all or optionally downsampled data to another InfluxDB 3 instance
- Compressed Queue: Stores compressed data in edr_queue.jsonl.gz locally to handle connection interruptions etc.
- Table Filtering: Replicate all or optionally specific tables.

## Setup, Run & Test

### 1. Install & Run InfluxDB v3 Core/Enterprise

- Download & Install from the official site or package manager.
- Make sure "plugins" directory exist otherwise create one ```mkdir ~/.plugins```
- Place [data-replicator.py](https://github.com/suyashcjoshi/influxdb3_plugins/blob/main/suyashcjoshi/data-replicator/data-replicator.py) in ~/.plugins/. The plugin dynamically uses its own directory for queuing (edr_queue.jsonl.gz) which it will create in same folder.


- Start InfluxDB 3 using cli by providing is the correct path to plugin and data directories as follows
  ```bash
  influxdb3 serve \
    --node-id host01 \
    --object-store file \
    --data-dir ~/.influxdb3 \
    --plugin-dir ~/.plugins


### 2. Download & Install InfluxDB 3 python module used by plugin 

```bash
influxdb3 install package influxdb3-python
```

### 3. Download & Install [Telegraf](https://docs.influxdata.com/telegraf/v1/install/) (optional)

### 4. Configure & Run Telegraf to write Data to InfluxDB 3 Core/Enterprise (optional)
Example script is for getting system metrics can be found [here](https://github.com/suyashcjoshi/influxdb3_plugins/blob/main/suyashcjoshi/data-replicator/telegraf.config) and run it using cli ```telegraf --config telegraf.conf```
Alternatively the plugin can be tested and run without telegraf as long as data is being written to InfluxDB 3 Core/Enterprise locally.

### 5. Create Trigger 

Using the following command we are creating a trigger for ["on WAL Flush"](https://docs.influxdata.com/influxdb3/core/#trigger) based on the plugin for all the tables inside database 'mydb'.

```bash
influxdb3 create trigger \
  -d mydb \
  --plugin-filename data-replicator.py \
  --trigger-spec "all_tables" \
  --trigger-arguments "host=YOUR_HOST_URL,token=YOUR_TOKEN,database=mydb,aggregate_interval=1m" \
  data_replicator_trigger
```

#### Arguments:

- tables: Comma-separated tables to replicate (e.g., cpu,mem). Omit for all.
- database: name of your database/bucket in your InfluxDB 3 instance where you want to replicate data (e.g. Cloud serverless URL)
- host: provide host URL for your InfluxDB 3 instance where you want to replicate (e.g. Cloud Serverless URL)
- token: provide authentication token for your InfluxDB 3 instance where you want to replicate the data (e.g Cloud Serverless API token)
- aggregate_interval: This is used to down sample data at given interval (e.g., 1m for 1-minute averages). Omit this for no downsampling.

### 6. Enable Trigger
```bash
influxdb3 enable trigger --database mydb data_replicator_trigger
```

### 7. Testing the plugin

#### Use Case 1: Complete data replication without Downsampling

**Clear Queue:**
```bash
rm ~/.plugins/edr_queue.jsonl.gz
```
**Run Telegraf** (Stop and run if already running)

```bash
telegraf --config telegraf.conf
```
**Run Telegraf for atleast 1 Minute**: Stop after using Ctrl + C

**Query Local InfluxDB 3 Instance**: Run SQL query using influxdb3 cli

```bash
influxdb3 query --database mydb "SELECT * FROM cpu WHERE cpu = 'cpu-total' AND time >= now() - interval '5 minutes' LIMIT 2"
```

**Query Serverless Instance**: Run the same SQL query for remote InfluxDB 3 instance for example using Data Explorer UI tool within InfluxDB 3 Cloud Serverless
```sql
SELECT * FROM cpu WHERE cpu = 'cpu-total' AND time >= now() - interval '5 minutes' LIMIT 2
```



#### Use Case 2: Data Replication With Downsampling

**Clear local queue**
```bash
rm ~/.plugins/edr_queue.jsonl.gz
```
**Create/Recreate Trigger** Enable downsampling by providing aggregate_interval=1m argument

```bash
influxdb3 create trigger \
  -d mydb \
  --plugin-filename data-replicator.py \
  --trigger-spec "all_tables" \
  --trigger-arguments "host=YOUR_HOST_URL,token=YOUR_TOKEN,database=mydb,tables=cpu,aggregate_interval=1m" \
  --error-behavior retry \
  data_replicator_trigger
```
**Enable Trigger**
```
influxdb3 enable trigger --database mydb data_replicator_trigger
```
**Stop & Restart Telegraf**
```bash
telegraf --config telegraf.conf
```
**Run Telegraf for atleast 2 Minutes**: Stop after using Ctrl + C

**Query Local Instance (No downsampling locally)**
```bash
influxdb3 query --database mydb "SELECT * FROM cpu WHERE cpu = 'cpu-total' AND time >= now() - interval '5 minutes' LIMIT 2"
```

**Query Remote InfludDB 3 Instance (Downsampled)**
```sql
SELECT * FROM cpu WHERE cpu = 'cpu-total' AND time >= now() - interval '5 minutes' LIMIT 2
```

## Questions/Comments

Hope this plugin use useful. If any questions/issues, please feel free to open a GitHub issue and find us  comments on [Discord](https://discord.com/invite/vZe2w2Ds8B) in the #influxdb3_core channel, [Slack](https://influxcommunity.slack.com/join/shared_invite/zt-2z3n3fs0i-jnF9Ag6NVBO26P98iY_h_g#/shared-invite/email) in the #influxdb3_core channel, or our [Community Forums](https://community.influxdata.com/).







