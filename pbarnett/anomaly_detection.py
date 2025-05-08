import requests
from collections import deque
from time import time
from statistics import mean, stdev
from datetime import datetime

def process_writes(influxdb3_local, table_batches, args=None):
    """
    Anomaly detection plugin that monitors table data and sends alerts
    to a Slack alert HTTP endpoint when anomalies are detected.
    
    Parameters:
    - influxdb3_local: The InfluxDB 3 Processing Engine API
    - table_batches: Batches of data being written
    - args: Configuration parameters from trigger arguments
    
    Required Arguments:
    - table_name: Name of the table to monitor
    - field_name: Name of the field to monitor for anomalies
    - slack_endpoint: URL of the Slack alert plugin endpoint
    
    Optional Arguments:
    - window_size: Number of points to include in analysis (default: 5)
    - z_score_threshold: Z-score threshold for anomaly detection (default: 2.0)
    - cooldown_seconds: Minimum time between alerts (default: 300)
    - alert_title: Title for Slack notifications (default: "Anomaly Alert")
    - min_datapoints: Minimum datapoints required before analysis (default: 5)
    """
    
    # Default configuration
    default_args = {
        "table_name": None,                 # Required
        "field_name": None,                 # Required
        "slack_endpoint": None,             # Required
        "window_size": "5",                 # Analysis window
        "z_score_threshold": "2.0",         # Detection sensitivity
        "cooldown_seconds": "300",          # 5 minutes between alerts
        "alert_title": "Anomaly Alert",     # Alert title
        "min_datapoints": "5"               # Minimum required data
    }

    # Merge with provided args
    args = args or {}
    config = {**default_args, **args}
    
    # Validate required parameters
    required_params = ["table_name", "field_name", "slack_endpoint"]
    for param in required_params:
        if not config[param]:
            influxdb3_local.error(f"Missing required parameter: {param}")
            return
    
    # Parse configuration
    try:
        table_name = config["table_name"]
        field_name = config["field_name"]
        slack_endpoint = config["slack_endpoint"]
        window_size = int(config["window_size"])
        z_score_threshold = float(config["z_score_threshold"])
        cooldown_seconds = int(config["cooldown_seconds"])
        alert_title = config["alert_title"]
        min_datapoints = int(config["min_datapoints"])
    except (ValueError, KeyError) as e:
        influxdb3_local.error(f"Configuration error: {str(e)}")
        return
    
    # Get cache keys
    values_key = f"values_{table_name}_{field_name}"
    last_alert_key = f"last_alert_{table_name}_{field_name}"
    
    # Retrieve cached data
    cached_values = influxdb3_local.cache.get(values_key, default=deque(maxlen=window_size))
    last_alert_time = influxdb3_local.cache.get(last_alert_key, default=0.0)
    
    # Ensure cached values has correct type and size
    if not isinstance(cached_values, deque) or cached_values.maxlen != window_size:
        cached_values = deque(maxlen=window_size)
    
    # Process incoming data
    for table_batch in table_batches:
        # Skip non-matching tables
        if table_batch["table_name"] != table_name:
            continue
            
        # Process rows in this batch
        for row in table_batch["rows"]:
            value = row.get(field_name)
            
            # Skip rows without the target field or non-numeric values
            if value is None or not isinstance(value, (int, float)):
                continue
                
            # Add value to the sliding window
            cached_values.append(value)
            
            # Check for anomalies if we have enough data
            if len(cached_values) >= min_datapoints:
                # Calculate statistics on all values except the current one
                previous_values = list(cached_values)[:-1]
                current_value = cached_values[-1]
                
                # Skip if not enough previous values
                if len(previous_values) < 2:
                    continue
                    
                # Calculate mean and standard deviation
                try:
                    avg = mean(previous_values)
                    std = stdev(previous_values)
                    
                    # Skip if standard deviation is too small (avoid division by zero)
                    if std < 0.0001:
                        continue
                        
                    # Calculate z-score
                    z_score = abs(current_value - avg) / std
                    
                    # Check if anomaly detected
                    if z_score > z_score_threshold:
                        # Check cooldown period
                        current_time = time()
                        if current_time - last_alert_time >= cooldown_seconds:
                            # Format alert message
                            direction = "increase" if current_value > avg else "decrease"
                            message = f"Anomaly detected: Sudden {direction} in {field_name}"
                            
                            # Prepare data for alert
                            alert_data = {
                                "Current Value": current_value,
                                "Average": f"{avg:.2f}",
                                "Standard Deviation": f"{std:.2f}",
                                "Z-Score": f"{z_score:.2f}",
                                "Threshold": z_score_threshold,
                                "Table": table_name,
                                "Field": field_name,
                                "Timestamp": datetime.now().isoformat()
                            }
                            
                            # Include additional context from the row if available
                            for key, value in row.items():
                                if key not in alert_data and key != "time" and key != field_name:
                                    # Only include scalar values
                                    if isinstance(value, (int, float, str, bool)):
                                        alert_data[key] = value
                            
                            # Send alert to Slack endpoint
                            send_slack_alert(
                                influxdb3_local,
                                slack_endpoint,
                                message,
                                alert_data,
                                alert_type="warning",
                                title=alert_title
                            )
                            
                            # Update last alert time
                            influxdb3_local.cache.put(last_alert_key, current_time)
                except Exception as e:
                    influxdb3_local.warn(f"Error in anomaly detection: {str(e)}")
    
    # Store updated values in cache
    influxdb3_local.cache.put(values_key, cached_values)


def send_slack_alert(influxdb3_local, endpoint, message, data, alert_type="warning", title="Anomaly Alert"):
    """
    Send an alert to the Slack alert plugin endpoint.
    
    Parameters:
    - influxdb3_local: The InfluxDB 3 Processing Engine API
    - endpoint: URL of the Slack alert plugin endpoint
    - message: Main message text
    - data: Dictionary of fields to include in the alert
    - alert_type: Alert type (info, warning, danger)
    - title: Title for the alert
    """
    try:
        # Prepare payload to match Slack alert plugin expectations
        payload = {
            "message": message,
            "alert_type": alert_type,
            "title": title,
            "fields": data
        }
        
        # Send to Slack alert endpoint
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Check response
        if response.status_code >= 200 and response.status_code < 300:
            influxdb3_local.info(f"Alert sent successfully: {message}")
        else:
            influxdb3_local.error(f"Failed to send alert: {response.status_code} - {response.text}")
            
    except Exception as e:
        influxdb3_local.error(f"Error sending alert: {str(e)}")