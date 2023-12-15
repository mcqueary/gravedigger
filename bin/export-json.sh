#!/bin/sh
sqlite3 $1 <<EOF
.headers on
.mode json
.output data.json
select * from graves;
.quit
EOF
