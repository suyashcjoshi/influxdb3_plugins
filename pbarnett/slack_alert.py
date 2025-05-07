import requests
import json
from datetime import datetime

# This was made in a few minutes with Claude in a project with the plugin documentation and 
# a couple of iterations. Its goal is to be a tightly focused Slack alert plugin.

def process_request(influxdb3_local, query_parameters, request_headers, request_body, args=None):
    """
    Generic Slack Alert Plugin - HTTP Webhook Endpoint

    This plugin accepts HTTP requests and transforms them into Slack notifications.
    It serves as a transducer that converts incoming alerts from any system into
    properly formatted Slack messages.

    Input Methods:
    - Supports both GET query parameters and POST JSON body
    - POST body takes precedence over query parameters

    REQUIRED Parameters:
    - webhook_url:    The Slack webhook URL to send notifications to
                        Can also be configured in trigger_arguments for security
    - message:        The main message text to display in the notification

    OPTIONAL Parameters:
    - alert_type:     Type of alert - "info" (default), "warning", or "danger"
                        Controls the color and icon of the notification
    - title:          Title to display in the notification (default: "InfluxDB Alert")
    - fields:         Dictionary of key-value pairs to include in the notification
                        (as JSON string in query parameters or object in request body)
    - metadata:       Dictionary of context information (displayed separately from fields)
                        (as JSON string in query parameters or object in request body)

    Trigger Arguments (args):
    - default_webhook_url:  Default Slack webhook URL if not provided in request
                        (recommended for security)
    - require_auth_token:   If "true", requires an auth_token parameter to match token_value
    - token_value:          The expected authentication token value
    - log_requests:         If "true", logs all incoming requests (default: "false")

    EXAMPLES:

    1. GET Request Example:
    /api/v3/engine/alert?webhook_url=https://hooks.slack.com/services/T00000/B00000/XXXXX
    &message=Disk%20space%20low%20on%20database%20server
    &alert_type=warning
    &title=Storage%20Alert
    &fields={"Server":"db-prod-1","Available":"2.3GB"}

    2. POST JSON Body Example:
    Endpoint: /api/v3/engine/alert
    
    {
        "webhook_url": "https://hooks.slack.com/services/T00000/B00000/XXXXX",
        "message": "Database backup failed",
        "alert_type": "danger",
        "title": "Backup Alert",
        "fields": {
        "Server": "db-prod-1",
        "Error Code": 500,
        "Available Space": "2.3 GB"
        },
        "metadata": {
        "Triggered By": "backup-scheduler",
        "Alert ID": "backup-failure-db1"
        }
    }

    Returns:
    - JSON response with status of the notification
    Success: {"status": "success", "message": "Alert sent successfully", "timestamp": "2025-05-04T10:15:30.123456"}
    Error: {"status": "error", "message": "Error description"}
    """

    # Initialize configuration
    args = args or {}
    default_webhook_url = args.get("default_webhook_url")
    require_auth = args.get("require_auth_token", "false").lower() == "true"
    expected_token = args.get("token_value")
    
    # Log request if enabled
    if args.get("log_requests", "false").lower() == "true":
        influxdb3_local.info(f"Received alert request: {query_parameters}")
        if request_body:
            influxdb3_local.info(f"Request body: {request_body[:200]}...")
    
    # Parse and merge request data (body takes precedence)
    body_data = {}
    if request_body:
        try:
            body_data = json.loads(request_body)
        except json.JSONDecodeError as e:
            influxdb3_local.error(f"Invalid JSON in request body: {str(e)}")
            return {"status": "error", "message": "Invalid JSON in request body"}
    
    params = {**query_parameters, **body_data}
    
    # Validate authentication if required
    if require_auth and params.get("auth_token") != expected_token:
        influxdb3_local.warn("Unauthorized alert request attempt")
        return {"status": "error", "message": "Unauthorized: Invalid or missing auth_token"}
    
    # Get and validate required parameters
    webhook_url = params.get("webhook_url") or default_webhook_url
    message = params.get("message")
    
    if not webhook_url:
        return {"status": "error", "message": "Missing required parameter: webhook_url"}
    if not message:
        return {"status": "error", "message": "Missing required parameter: message"}
    
    # Process optional parameters
    alert_type = params.get("alert_type", "info")
    title = params.get("title", "InfluxDB Alert")
    
    # Extract fields and metadata
    fields = parse_json_param(params.get("fields"), "fields", influxdb3_local)
    metadata = parse_json_param(params.get("metadata"), "metadata", influxdb3_local)
    
    # Send notification
    try:
        blocks = format_slack_message(message, {**fields, **metadata}, alert_type, title)
        response = send_to_slack(influxdb3_local, webhook_url, blocks)
        
        if 200 <= response.status_code < 300:
            influxdb3_local.info(f"Alert sent successfully: {message}")
            return {
                "status": "success",
                "message": "Alert sent successfully",
                "timestamp": datetime.now().isoformat()
            }
        
        error_msg = f"Failed to send alert: HTTP {response.status_code} - {response.text}"
        influxdb3_local.error(error_msg)
        return {"status": "error", "message": error_msg}
            
    except Exception as e:
        error_msg = f"Error sending alert: {str(e)}"
        influxdb3_local.error(error_msg)
        return {"status": "error", "message": error_msg}


def parse_json_param(param, param_name, logger):
    """Helper to parse JSON parameters that might be strings or dicts"""
    if isinstance(param, dict):
        return param
    
    if isinstance(param, str):
        try:
            return json.loads(param)
        except json.JSONDecodeError:
            logger.warn(f"Invalid JSON in {param_name} parameter")
    
    return {}


def format_slack_message(message, data, alert_type="info", title="InfluxDB Alert"):
    """Formats a Slack message with consistent styling."""
    # Map alert types to colors and emojis
    styles = {
        "info": {"color": "#36C5F0", "emoji": ":information_source:"},
        "warning": {"color": "#ECB22E", "emoji": ":warning:"},
        "danger": {"color": "#E01E5A", "emoji": ":exclamation:"}
    }
    
    style = styles.get(alert_type, styles["info"])
    
    # Build Slack blocks for the message
    blocks = [
        # Header with alert type and emoji
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{style['emoji']} {title}",
                "emoji": True
            }
        },
        # Main message with emphasis
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{message}*"
            }
        }
    ]
    
    if data:
        # Split data into standard fields and metadata
        metadata_keys = ["Table", "Field", "Triggered By", "Alert ID", "Source"]
        fields = {k: v for k, v in data.items() if k not in metadata_keys}
        metadata = {k: v for k, v in data.items() if k in metadata_keys}
        
        # Add fields as a structured section
        if fields:
            field_blocks = [
                format_field_block(key, value) for key, value in fields.items()
            ]
            
            # Slack limits to 10 fields per section
            blocks.append({"type": "section", "fields": field_blocks[:10]})
            
            # Handle additional fields if more than 10
            if len(field_blocks) > 10:
                additional_fields = "\n".join([
                    format_field_text(key, value) for key, value in list(fields.items())[10:]
                ])
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": additional_fields}
                })
        
        # Add metadata as a separate section
        if metadata:
            metadata_text = "\n".join(f"_{key}:_ {value}" for key, value in metadata.items())
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": metadata_text}
                }
            )
    
    # Add divider and timestamp
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
        ]
    })
    
    return blocks


def format_field_block(key, value):
    """Format a single field for Slack blocks"""
    return {
        "type": "mrkdwn",
        "text": format_field_text(key, value)
    }


def format_field_text(key, value):
    """Format field text with proper formatting for different value types"""
    if isinstance(value, float) and not isinstance(value, bool):
        return f"*{key}:* {value:.2f}"
    return f"*{key}:* {value}"


def send_to_slack(logger, webhook_url, blocks):
    """Sends formatted blocks to Slack webhook URL."""
    return requests.post(
        webhook_url,
        headers={"Content-Type": "application/json"},
        json={"blocks": blocks}
    )