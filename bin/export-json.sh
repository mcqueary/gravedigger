#!/bin/sh
sqlite3 graves.db <<EOF
.headers on
.mode json
.output data.json
select * from graves;
.quit
EOF
