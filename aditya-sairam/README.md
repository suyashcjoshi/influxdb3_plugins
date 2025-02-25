# **Python Plugins for Processing Engine**

This **WAL plugin** automatically collects statistical metrics for a table whenever data is written to it. It generates a new table that records the following statistics for each numerical column:

- **Min**, **Max**  
- **Mean**, **Median**, **Mode**  
- **95th Percentile**  

This functionality is similar to the `.describe()` method in Python, which summarizes numerical columns in a DataFrame.

## **Prerequisites**

Ensure a database exists before using the plugin:

```bash
influxdb3 create database <database_name>
```

## **Setting Up the Trigger**

Once the database is created, set up the trigger with the following command:(Make sure to include the table for which you want to collect the statistics in **--trigger-spec** and **--trigger-arguments**)

```bash
influxdb3 create trigger \
  --database <database-name> \
  --trigger-spec 'table:<table-name>' \
  --trigger-arguments 'table_name:<table-name>' \
  --plugin-filename <path-to-file>/stats_metrics.py stats_metrics_trigger
```

## **Enabling the Trigger**

After creating the trigger, enable it to start capturing statistical metrics whenever new data is written:

```bash
influxdb3 enable trigger --database <database-name> stats_metrics_trigger
```

Write data into the database using:

```bash
influxdb3 write --database <database-name> --file <lp-file-name.lp>
```

## **Generated Table Example**

When data is written to the specified table (e.g., `sensor_data`), the plugin creates a corresponding analytics table (`analytics_<table-name>`) that stores computed statistics:

```bash
------------+--------------------+--------------------+-----------------------+--------------------+--------------------+---------------------+
| field_name | min                | max                | mean                  | median             | mode               | 95th_percentile    |
+------------+--------------------+--------------------+-----------------------+--------------------+--------------------+--------------------+
| co         | 0.0011705085484379 | 0.0072680285963655 | 0.004494020980943046  | 0.0043415449971564 | 0.0014023067180012 | 0.0067827228544403 |
| humidity   | 16.600000381469727 | 92.0               | 63.77917173040387     | 60.70000076293945  | 77.19999694824219  | 79.30000305175781  |
| light      | 0.0                | 1.0                | 0.25358220551831306   | 0.0                | 0.0                | 1.0                |
| lpg        | 0.0026934786226618 | 0.0100926106082718 | 0.0069926626347598594 | 0.006952254607111  | 0.003069572712416  | 0.0096004658551668 |
| motion     | 0.0                | 1.0                | 0.000831180095043637  | 0.0                | 0.0                | 0.0                |
| smoke      | 0.0066920963173865 | 0.0274389440348949 | 0.018612339797727463  | 0.0184269059272954 | 0.0076947918250824 | 0.0260121274822193 |
| temp       | 0.3000000119209289 | 28.899999618530273 | 22.259955209882623    | 22.2               | 22.2               | 27.600000381469727 |
+------------+--------------------+--------------------+-----------------------+--------------------+--------------------+--------------------+
```

