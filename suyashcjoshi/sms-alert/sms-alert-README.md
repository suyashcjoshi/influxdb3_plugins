## InfluxDB 3 Core/Enterprise SMS alerts plugin

This plugin sends SMS alerts via Twilio based on for any given threshold conditions with for  InfluxDB 3 Core/Enterprise. For example you can use the WAL Flush trigger to send an alert SMS when a threhold value exceeds for example temp > 100 

## Prerequisites

*   InfluxDB 3.0 Core/Enterprise running.
*   A Twilio account with an active phone number (free trial)
*   The `twilio` Python library installed (`influxdb3 install package twilio`).
*   The `python-dotenv` library installed (`influxdb3 install package python-dotenv`) - *Required for development using a `.env` file*.

## Installation

1.  **Place the Plugin File:** Place the `sms-alert.py` file in your InfluxDB 3.0 plugin directory.

2.  **Install Dependencies using influxdb3 provided python support:**
    ```bash
    influxdb3 install package twilio
    influxdb3 install package python-dotenv
    ```

## Configuration

**1. Environment Variables (Required):**

 Open the file named `.env` and update the values with your Twilio credentials. 

    ```
    TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    TWILIO_AUTH_TOKEN=your_auth_token
    TWILIO_FROM_NUMBER=+15551234567
    TWILIO_TO_NUMBER=+15557654321
    ```

## WAL Flush Trigger Setup & Test

### 1. Create it (modify arguments as per your logic)
```bash
influxdb3 create trigger \
  --trigger-spec "all_tables" \
  --plugin-filename "sms-alert.py" \
  --database mydb2 \
  wal_alert \
  --trigger-arguments "field_name=temperature,threshold=80"
```

#### 2. Enable it
```bash
influxdb3 enable trigger --database mydb wal_alert
```

#### 2. Test it
```bash
influxdb3 test wal_plugin \
  --lp "weather,location=us-midwest temperature=90i 1678886400000000000" \
  --input-arguments "field_name=temperature,threshold=80" \
  --database mydb \
  sms-alert.py
```

![SMS Alert Screenshot](./sms-screenshot.png)

