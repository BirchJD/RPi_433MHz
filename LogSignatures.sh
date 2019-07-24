find LOG/ -name '*.log' -exec grep -a 'RX SIGNATURE:' {} \; | sort | uniq -c | sort -n

