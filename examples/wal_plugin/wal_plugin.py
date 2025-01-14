# This is an example WAL plugin that reads through data and writes 
# a record to another table about the number of rows we see in 
# each WAL flush for each table. It also shows using arguments 
# associated with the trigger to drive plugin behavior.

def process_writes(influxdb3_local, table_batches, args=None):
    for table_batch in table_batches:
        # Skip if table_name is write_reports
        if table_batch["table_name"] == "write_reports":
            continue

        row_count = len(table_batch["rows"])

        # Double row count if table name matches args table_name
        if args and "double_count_table" in args and table_batch["table_name"] == args["double_count_table"]:
            row_count *= 2

        line = LineBuilder("write_reports")\
            .tag("table_name", table_batch["table_name"])\
            .int64_field("row_count", row_count)
        influxdb3_local.write(line)

    influxdb3_local.info("wal_plugin.py done")
