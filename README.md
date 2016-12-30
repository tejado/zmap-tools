# zmap-tools
A small tool collection for zmap to collect and analyse data.

## zscan.sh
Wrapper around zmap and zgrab to scan for specific http/https ports over a specific IP network range list.
```shell
$ ./zscan.sh ip-list.txt output.txt
```

## zdata.py
Parsing the output file of zscan.sh in different ways, e.g. searching for webserver directory listings ("Index of /") including a recursive directory structure.

```shell
$ ./zdata.py --help
```

## Disclaimer
These tools were created during long nights with a lot of drinks at the 33c3.  
Feel free to improve them in any way!
