from typing import List, Dict, Any, Optional, Tuple
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MESSAGE_TEMPLATE = "Alert: {message_content}"

# Helper function to send SMS alert via Twilio
def send_sms(account_sid: str, auth_token: str, from_number: str, to_number: str, message_body: str) -> bool:
    """Sends an SMS message using Twilio."""
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            to=to_number,
            from_=from_number,
            body=message_body
        )
        print(f"SMS sent! SID: {message.sid}")
        return True
    except TwilioRestException as e:
        print(f"Twilio error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def get_config(args: Optional[Dict[str, str]]) -> Tuple[bool, Dict[str, Any]]:
    """Gets configuration from environment variables and overrides with arguments."""
    config = {}
    errors = []

    # Twilio Credentials from environment variables
    config["account_sid"] = os.environ.get("TWILIO_ACCOUNT_SID")
    config["auth_token"] = os.environ.get("TWILIO_AUTH_TOKEN")
    config["from_number"] = os.environ.get("TWILIO_FROM_NUMBER")
    config["to_number"] = os.environ.get("TWILIO_TO_NUMBER")

    if not all([config["account_sid"], config["auth_token"], config["from_number"], config["to_number"]]):
        errors.append("Missing required environment variables: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TWILIO_TO_NUMBER")

    if args:
        # Override Twilio credentials if provided in arguments
        config["account_sid"] = args.get("twilio_account_sid", config["account_sid"])
        config["auth_token"] = args.get("twilio_auth_token", config["auth_token"])
        config["from_number"] = args.get("twilio_from_number", config["from_number"])
        config["to_number"] = args.get("twilio_to_number", config["to_number"])
        # Common Arguments
        config["message_template"] = args.get("message", DEFAULT_MESSAGE_TEMPLATE)
        config["field_name"] = args.get("field_name")
        config["threshold"] = args.get("threshold")
        if not config.get("field_name"):
            errors.append("Missing required argument for WAL trigger: field_name")
        if not config.get("threshold"):
            errors.append("Missing required argument for WAL trigger: threshold")
        else:
            try:
                config["threshold"] = float(config["threshold"])
            except ValueError:
                errors.append("Invalid 'threshold' argument. Must be a number.")
    else:
      errors.append("No arguments were provided")

    if errors:
        return False, {"errors": errors}
    return True, config


def process_wal_flush(influxdb3_local, table_batches: List[Dict[str, Any]], config: Dict[str, Any]):
    """Handles WAL flush events, checking for a field exceeding a threshold."""

    sms_sent = False
    for table_batch in table_batches:
        table_name = table_batch["table_name"]
        influxdb3_local.info(f"Table: {table_name}")

        for row in table_batch["rows"]:
            if config["field_name"] in row:
                try:
                    field_value = float(row[config["field_name"]])
                except (ValueError, TypeError):
                    influxdb3_local.warn(f"Field '{config['field_name']}' is not a number. Skipping.")
                    continue

                if field_value > config["threshold"] and not sms_sent:
                    influxdb3_local.warn(f"Field '{config['field_name']}' exceeded threshold: {field_value} > {config['threshold']}")

                    message = config["message_template"].format(
                        message_content = f"{config['field_name']} ({field_value}) exceeded threshold ({config['threshold']})",
                        field_name=config["field_name"],  
                        field_value=field_value,          
                        threshold=config["threshold"],      
                        timestamp=row.get('time', 'N/A')
                    )

                    if send_sms(config["account_sid"], config["auth_token"], config["from_number"], config["to_number"], message):
                        influxdb3_local.info("SMS sent.")
                        sms_sent = True
                    else:
                        influxdb3_local.error("Failed to send SMS.")


# Entry point for WAL-triggered logic
def process_writes(influxdb3_local, table_batches: List[Dict[str, Any]], args: Optional[Dict[str, str]] = None):
    """Entry point for WAL-triggered logic."""
    success, config = get_config(args, "wal")  # Pass "wal" as trigger_type
    if not success:
        for error in config["errors"]:
            influxdb3_local.error(error)
        return
    process_wal_flush(influxdb3_local, table_batches, config)
