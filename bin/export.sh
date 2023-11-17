#!/bin/sh
sqlite3 graves.db <<EOF
.headers on
.mode csv
.output data.csv
select * from graves;
.quit
EOF
