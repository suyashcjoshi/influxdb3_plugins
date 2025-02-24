## Python Plugins for Processing Engine

This Schedule plugin is made for scraping Prometheus endpoint and write metrics back to influxdb3.

It needs just a couple of `import`s:

```bash
$ influxdb3 install package requests
$ influxdb3 install package prometheus_client
```

After you've created a DB for the trigger with:

```bash
$ influxdb3 create database metrics
```

You could then create the trigger:

```bash
influxdb3 create trigger --trigger-spec "every:10s" --plugin-filename <path_to_file>/prometheus_metrics.py --database metrics --trigger-arguments "hostname=localhost,ip_address=100.100.100.100,port=80" tailscale-localhost-metrics
```

In the above example, it creates a schedule trigger that scrapes your local Tailscaled service (more here https://tailscale.com/kb/1482/client-metrics) such that you can have:

```bash
➜ influxdb3 query --database=metrics "SELECT path,value,time FROM tailscaled_inbound_bytes_total WHERE host='localhost' AND path='derp' ORDER BY time ASC"
+------+-----------+-------------------------------+
| path | value     | time                          |
+------+-----------+-------------------------------+
| derp | 2681308.0 | 2025-02-24T09:35:50.027185292 |
| derp | 2688844.0 | 2025-02-24T09:36:00.027418810 |
| derp | 2696380.0 | 2025-02-24T09:36:10.016980230 |
| derp | 2703916.0 | 2025-02-24T09:36:20.018751834 |
| derp | 2711452.0 | 2025-02-24T09:36:30.021800981 |
| derp | 2719324.0 | 2025-02-24T09:36:40.023237792 |
+------+-----------+-------------------------------+
```

