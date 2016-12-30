# zmap-tools
A small tool collection for ZMap to collect and analyse data.

## zscan.sh
Wrapper around ZMap and ZGrab  to scan for specific http/https ports over a specific IP network range list.
```shell
$ ./zscan.sh ip-list.txt output.txt
```

## zdata.py
Parsing the output file of zscan.sh in different ways, e.g. searching for webserver directory listings ("Index of /") including a recursive directory structure.

```shell
$ ./zdata.py --help
```

## ???
"[ZMap](https://zmap.io/) is an open-source network scanner that enables researchers to easily perform Internet-wide network studies. With a single machine and a well provisioned network uplink, ZMap is capable of performing a complete scan of the IPv4 address space in under 5 minutes, approaching the theoretical limit of ten gigabit Ethernet." zmap.io, 2016.

## Disclaimer
These tools were created during long nights with a lot of drinks at the 33c3.  
Feel free to improve them in any way!
