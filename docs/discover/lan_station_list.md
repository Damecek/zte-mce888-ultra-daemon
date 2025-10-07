# ZTE Discover Example

## Request
Host: 192.168.0.1
Path: goform/goform_get_cmd_process?isTest=false&cmd=lan_station_list
Method: GET

```json
null
```

## Response
```json
{
  "lan_station_list": [
    {
      "mac": "AA:BB:CC:DD:EE:FF",
      "ip": "192.168.0.101",
      "hostname": "laptop",
      "connected": true
    },
    {
      "mac": "11:22:33:44:55:66",
      "ip": "192.168.0.102",
      "hostname": "smart-tv",
      "connected": false
    }
  ]
}
```
