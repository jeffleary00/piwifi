# piwifi
Python module to manage wpa_supplicant wifi networks on Raspberry Pi

# installation
sudo pip3 install piwifi

# usage
```
  from piwifi import Scanner, WpaManager

  s = Scanner(sudo=True)
  print(s.cells)
  print(s.quietest_channel())

  m = WpaManager(sudo=True)
  m.list_networks()
  m.add_network( { 'ssid': 'Some Wifi', 'scan_ssid': 1, 'psk': 'wpa2password'} )
  m.delete_network(3)
```

# todo
Tests needed, of course. And some better exception and error handling too. Make a pull request if you would like to contribute! Thanks!

# caveats
The wpa_supplicant python looks far more complete. However, I could not get it to work, even with the most basic examples and tests. So, I abandoned it and wrote this module to quickly and easily meet my needs.

This module's classes are simply wrappers around the wpi_cli, wpa_passphrase, and iwlist commands. A bit crude, but it allows a non-root user (with appropriate sudo permissions) to manage the wifi networks.
