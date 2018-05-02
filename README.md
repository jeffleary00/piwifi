# piwifi
Python module to manage wpa_supplicant wifi networks on Raspberry Pi

# installation
```
sudo pip3 install piwifi
```

# usage
```
  from piwifi import Scanner, WpaManager

  s = Scanner(interface='wlan0', sudo=True)
  print(s.cells)
  print(s.quietest_channel())
  print(s.strongest_channel())

  m = WpaManager(sudo=True)
  m.list_networks()
  m.add_network( {'ssid': 'Some Wifi', 'scan_ssid': 1, 'psk': 'wpa2password'} )
  m.set_network(1, 'psk', 'newpassword')
  m.delete_network(3)
  m.enable_network(1)
  m.save_config()
```

# todo
Tests needed, of course. And some better exception and error handling too. Make a pull request if you would like to contribute! Thanks!

# caveats
- Tested with Raspbian 'Stretch'. YMMV

- The wpa_supplicant python looks far more complete, and you should probably be using that module instead. 
However, I could not get it to work, even with the most basic examples and tests. So, I abandoned it and wrote this module to quickly and easily meet my needs.

- This module's classes are simply wrappers around the wpi_cli, wpa_passphrase, and iw list commands. A bit crude, but it allows a non-root user (with appropriate sudo permissions) to manage the wifi networks.

- Although this is intended for Raspberry Pi installs, it should probably work for most Linux systems.
