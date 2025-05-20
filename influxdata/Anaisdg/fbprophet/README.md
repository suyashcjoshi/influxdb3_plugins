# Wikipedia page traffic forecast with Prophet and InfluxDB 3 Core

This project uses **InfluxDB 3 Core's Processing Engine** and **FB Prophet** to forecast pageviews of the Wikipedia article for famous American footballer [Peyton Manning](https://en.wikipedia.org/wiki/Peyton_Manning).

It consists of the following plugins:

1. **[load_peyton_data.py](load_peyton_data.py)** – Fetches historical data and writes it to InfluxDB  
2. **[forecast_peyton.py](forecast_peyton.py)** – Trains a Prophet model and writes the forecast back to InfluxDB
3. **[plot_forecast_http.py](plot_forecast_http.py)** - Displays a graph of the historical data and forecast

---

### Pre-Requisites:

1. **Python**: Make sure you have Python version 3.x on your system.
2. **Code Editor**: Your favorite code editor.
3. **Install InfluxDB 3**: Either InfluxDB 3 Core or Enterprise.
   - You can install it as a `Docker Image` or directly using `Simple Download` option.
   - When promoted **Start InfluxDB Now? Type 'n'** as we will start it later.

   InfluxDB 3 Core
   ```shell
   curl -O https://www.influxdata.com/d/install_influxdb3.sh && sh install_influxdb3.sh
   ```
   InfluxDB 3 Enterprise
   ```shell
   curl -O https://www.influxdata.com/d/install_influxdb3.sh && sh install_influxdb3.sh enterprise
   ```
4. **Verify installation**: Open terminal window and run `influxdb3 --version` command without error to the latest version installed successfully.

5. **Configure Plugin**: To enable the Processing Engine, you need to tell InfluxDB where to find your Python plugin files. Use the `--plugin-dir` option when starting the server. Create a plugin directory anywhere you prefer as this is where plugin code will reside. Optionally, you also reference plugin from a GitHub repository in which case you can omit directory creation and start InfluxDB 3 without providing it plugin folder path.
   
```shell
cd ~
mkdir influxdb3-plugins
```

6. **Start InfluxDB 3 Core**
   
Arguments:

- `--node-id`: Identifier for your InfluxDB node.
- `--object-store`: Type of object storage (e.g., memory, file, remote such as Amazon S3).
- `--data-dir`: Location of the directory where file baed object storage will reside.
- `--plugin-dir`: Directory containing local Python plugin scripts. Omit this argument if using plugins directly from GitHub.

**Example command**
```shell
influxdb3 serve \
  --node-id node0 \
  --object-store file \
  --data-dir ~/.influxdb/data
  --plugin-dir ~/influxdb3-plugins
```
Upon running the command, InfluxDB 3 should start on localhost:8181 (default) and start printing logs in the terminal window without any error.

7. **Create a Token using the CLI**

Most `influxdb3` commands require an authentication token that give previleged access to the database operations. Create an admin token using the following command and save it somewhere securely as you will not be able to re-create it if lost.

Create an admin token
```shell
influxdb3 create token --admin
```

> [!TIP]
> Set the token as an environment variable to simplify repeated CLI commands: 
```shell
export INFLUXDB3_AUTH_TOKEN=YOUR_ADMIN_TOKEN
```

8. **Create Database**: Let's create and verfify the database. It can also be created automatically when line protocol data is first written to it.
```shell
influxdb3 create database my_awesome_db
influxdb3 show databases
```

9. **Write Sample Data**
    
```shell
influxdb3 write \
  --database my_awesome_db \
  --precision ns \
  'cpu,host=server01,region=us-west value=0.64 1641024000000000000'
```

10. **Query Data**
```shell
influxdb3 query \
  --database my_awesome_db \
  "SELECT * FROM cpu"
``` 

## 🧩 Plugins Overview

### Plugin & Triggers

A plugin is a Python file containing a callback function with a specific signature that corresponds to the trigger type. The trigger defines and configures the plugin including providing any optional information using `--trigger-arguments` option. One or more trigger can be setup to run simultaneously either synchnorously (default behavior) or asynchnorously. Triggers can also be disabled or deleted.

#### Install Python dependencies (optional)

InfluxDB 3 provides a virtual enviornment for running python processing engine plugins. Those plugins are often dependent on python packages such as those from PyPy. They can be installed using influxdb3 cli for example `influxdb3 install package pandas --token YOUR_TOKEN_STRING` to install pandas package.


### 1️⃣ `load_peyton_data.py`

- HTTP-triggered plugin  
- Downloads a public CSV of daily Wikipedia views  
- Writes rows to the `peyton_views` table in InfluxDB  

Trigger this manually via `curl` or any HTTP request.

### 2️⃣ `forecast_peyton.py`

- Scheduled plugin (runs daily or on your schedule)  
- Reads data from `peyton_views`  
- Fits a Prophet model  
- Forecasts 365 days into the future  
- Writes summary forecast results to `prophet_forecast`  

### 3️⃣ `plot_forecast_http.py`
- HTTP-triggered plugin  
- Reads data from both `peyton_views` and `prophet_forecast`  
- Creates an interactive Plotly chart combining historical data and forecast  
- Returns the chart as HTML for browser viewing

---

## ⚙️ Plugin Setup Instructions

### ✅ Step 1: Install Required Packages

This project depends on `plotly` and `prophet`. Install them using:
```bash 
influxdb3 install package plotly
```
```bash
influxdb3 install package prophet
```
Create a database:
```bash
influxdb3 create database prophet
```
### ✅ Step 2: Save the Plugins
Place both plugins in your configured --plugin-dir:
- load_peyton_data.py
- forecast_peyton.py
- plot_forecast_http.py
  
### ✅ Step 3: Create Triggers
#### Plugin 1: Load Data via HTTP
```bash
influxdb3 create trigger \
  --trigger-spec "request:load_peyton" \
  --plugin-filename "load_peyton_data.py" \
  --database prophet \
  load_peyton
```
Then trigger it manually:

```bash
curl http://localhost:8181/api/v3/engine/load_peyton
```
You should see the following output:
```bash
{"status": "success", "rows_written": 2905}
```
#### Plugin 2: Forecast on a Schedule
```bash
influxdb3 create trigger \
  --trigger-spec "every:1d" \
  --plugin-filename "forecast_peyton.py" \
  --database prophet \
  peyton_forecast
```
To disable the forecasting:
```bash
inflxudb3 disable trigger --databse prophet peyton_forecast
```

#### Plugin 3: Visualize Forecast via HTTP
```bash 
influxdb3 create trigger \
  --trigger-spec "request:plot_forecast" \
  --plugin-filename "plot_forecast_http.py" \
  --database prophet \
  forecast_plot
```
---
## 📊 Output

### Tables

- **`peyton_views`**: Raw historical pageview data  
- **`prophet_forecast`**: All forecasts made by prophet

### Graph 
View in your browser:
```
http://localhost:8181/api/v3/engine/plot_forecast
```
![visualization](img/graph.png)

---

## 🧠 How It Works

- **Prophet** is a time series forecasting library from Facebook that supports trends, seasonality, and uncertainty modeling.  
- **InfluxDB’s Processing Engine** allows you to embed Python directly inside the database.  
- You can build similar plugins to forecast your own metrics, user traffic, sales data, or anything time-based!
