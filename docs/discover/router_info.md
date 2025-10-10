# Discover Example: /goform/goform_get_cmd_process?isTest=false&cmd=lan_ipaddr%2Clan_netmask%2Cmac_address%2CdhcpEnabled%2CdhcpStart%2CdhcpEnd%2CdhcpLease_hour%2Cmtu%2Ctcp_mss%2Cdhcpv6stateEnabled&multi_data=1

## Request
```json
{
  "host": "http://192.168.0.1",
  "method": "GET",
  "path": "/goform/goform_get_cmd_process?isTest=false&cmd=lan_ipaddr%2Clan_netmask%2Cmac_address%2CdhcpEnabled%2CdhcpStart%2CdhcpEnd%2CdhcpLease_hour%2Cmtu%2Ctcp_mss%2Cdhcpv6stateEnabled&multi_data=1",
  "payload": null
}
```

## Response
```json
{
  "dhcpEnabled": "1",
  "dhcpEnd": "192.168.0.254",
  "dhcpLease_hour": "24",
  "dhcpStart": "192.168.0.2",
  "dhcpv6stateEnabled": "",
  "lan_ipaddr": "192.168.0.1",
  "lan_netmask": "255.255.255.0",
  "mac_address": "",
  "mtu": "1500",
  "tcp_mss": "1460"
}
```
