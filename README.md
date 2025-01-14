# InfluxDB 3 Plugins
This repo contains publicly shared plugins for InfluxDB 3. Users of either InfluxDB 3 Core or InfluxDB 3 Enterprise can install these plugins with a single command from the CLI.

Plugins should reside in their own directory underneath a another directory which signifies the organization, user or some other meaningful grouping. For example:

```
influxdata/getting_started/getting_started.py
examples/system/system_metrics.py
```

The Python file should have the same name as its parent directory. The plugin directory may contain other files such as test input data, test data to write into a database ahead of running the plugin's test suite, and output verification files.

All plugins in this repo are dual licensed MIT or Apache 2 at the user's choosing, unless a LICENCE file is in the plugin's directory.
