import ast
import requests
from prometheus_client.parser import text_string_to_metric_families


# Build LP from Prometheus data
def collect_metrics(influxdb3_local, hostname, ip_address, port, path):
  try:
    node_url = "http://%s:%s%s" % (ip_address, port, path)
    response = requests.get(node_url, timeout=5)
  except requests.exceptions.RequestException as err:
    raise SystemExit(err)

  data = response.text
  for family in text_string_to_metric_families(data):
    for sample in family.samples:

      name = '{0}'.format(*sample)
      tag = '{1}'.format(*sample)
      val = '{2}'.format(*sample)

      if val in ['nan','NaN','+inf','+Inf','-inf','-Inf']:
        continue

      value = float(val)
      tag_dict = ast.literal_eval(tag)

      line = LineBuilder(name)\
          .tag("host", hostname)

      if tag_dict:
        for k,v in tag_dict.items():
          line.tag(k, v)

      line.float64_field("value", value)

      influxdb3_local.write(line)

  return


def process_scheduled_call(influxdb3_local, time, args=None):
  try:
      # Set defaults or get from args
      hostname = args.get("hostname", "localhost") if args else "localhost"
      ip_address = args.get("ip_address", "127.0.0.1") if args else "127.0.0.1"
      port = args.get("port", "80") if args else "80"
      path = args.get("path", "/metrics") if args else "/metrics"

      collect_metrics(influxdb3_local, hostname, ip_address, port, path)
      influxdb3_local.info(f"Successfully collected metrics for host: {hostname}")

  except Exception as e:
      influxdb3_local.error(f"Error collecting system metrics: {str(e)}")

