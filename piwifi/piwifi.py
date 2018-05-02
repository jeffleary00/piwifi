import re
import subprocess


class PiCommander(object):
    def __init__(self, **kwargs):
        self.sudo_path = '/usr/bin/sudo'
        
        allowed = ['sudo_path']
        for k, v in kwargs.items():
            if k in allowed:
                setattr(self, k, v)


    def run_command(self, commands, sudo=False):
        if sudo:
            commands = [self.sudo_path] + commands
    
        child = subprocess.Popen(
            commands, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE)
    
        output, errors = child.communicate()
        return (child.returncode, output, errors) 
    
    

"""
===============================================================================
Scanner() class

Scan wifi networks
User should be root, or have permissions to run /sbin/iwlist as root with sudo.
===============================================================================
"""
class Scanner(PiCommander):
    def __init__(self, **kwargs):
        super(Scanner, self).__init__(**kwargs)
        self.sudo = False
        self.iwlist = '/sbin/iwlist'
        self.interface = 'wlan0'
        
        allowed = ['sudo', 'iwlist', 'interface']
        for k, v in kwargs.items():
            if k in allowed:
                setattr(self, k, v)
                
        self.scan()
    
    
    """
    Scan wireless networks and collect data
    params:
        interface=<nic name to scan>
        
    """
    def scan(self):
        self.cells = []
        cmd = [self.iwlist, self.interface, "scan"]
        rval, out, err = self.run_command(cmd, self.sudo)    
        content = out.decode('utf-8')
        
        return self.parse(content)
    
    
    """
    parse the results of a scan into networks
    
    params:
        1. text results from scan
    returns:
        void
    """
    def parse(self, content):
        network = {}
        cellre = re.compile(r"^Cell\s+(?P<cellnumber>.+)\s+-\s+Address:\s(?P<mac>.+)$")
        regexps = [
            re.compile(r"^ESSID:\"(?P<essid>.*)\"$"),
            re.compile(r"^Protocol:(?P<protocol>.+)$"),
            re.compile(r"^Mode:(?P<mode>.+)$"),
            re.compile(r"^Frequency:(?P<frequency>[\d.]+) (?P<frequency_units>.+) \(Channel (?P<channel>\d+)\)$"),
            re.compile(r"^Encryption key:(?P<encryption>.+)$"),
            re.compile(r"^Quality=(?P<signal_quality>\d+)/(?P<signal_total>\d+)\s+Signal level=(?P<signal_level_dBm>.+) d.+$"),
            re.compile(r"^Signal level=(?P<signal_quality>\d+)/(?P<signal_total>\d+).*$"),
            re.compile(r"IEEE\s+(?P<ieee>802.11.+)"),
        ]
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            cnum = cellre.search(line)
            
            if cnum is not None:
                self.cells.append(cnum.groupdict())
                continue
                
            for expression in regexps:
                result = expression.search(line)
                if result is not None:
                    self.cells[-1].update(result.groupdict())
                    continue
    

    """
    Return number of cell instances found on a particular channel number.
    
    Not really sure what this method was for. Must have seemed like a good idea
    at the time?
    
    params:
        a channel number
    returns:
        a number
    """          
    def channel_instances(self, chan):
        tally = 0
        for n in self.cells:
            if int(n['channel']) == int(chan):
                tally += 1
                
        return tally
    
    
    """
    Identify which wifi channel in the area is the 'cleanest' or least crowded.
    This is useful if you want to create an ad-hoc access-point.
    
    params:
        none
    returns:
        a channel number (int)
    """
    def quietest_channel(self):
        chan = 1
        lowest = 100
        
        scores = {key: 0 for key in range(1, 12)}
        for c in self.cells:
            scores[int(c['channel'])] += 1
            
            # weight stronger channels more than weaker ones.
            # there is no science to this. I just made it up.
            if int(c['signal_level_dBm']) > -50:
                scores[int(c['channel'])] += 3  
            elif int(c['signal_level_dBm']) > -60:
                scores[int(c['channel'])] += 1
            elif int(c['signal_level_dBm']) > -70:
                scores[int(c['channel'])] += .5
            elif int(c['signal_level_dBm']) > -80:
                scores[int(c['channel'])] += .25
            elif int(c['signal_level_dBm']) > -90:
                scores[int(c['channel'])] += .1
        
        # pick channel with lowest score         
        for k, v in scores.items():
            if v < lowest:
                chan = k
                lowest = v
                
        return chan


    """
    Identify which wifi channel in the area is the 'strongest' signal.
    
    params:
        none
    returns:
        a channel number (int)
    """
    def strongest_channel(self):
        chan = 1
        strongest = -180
        
        for c in self.cells:
            if int(c['signal_level_dBm']) > strongest:
                chan = int(c['channel'])
                strongest = int(c['signal_level_dBm'])
                        
        return chan



"""
===============================================================================
WpaManager() class

Manage wpa_supplicant network info.
User should be root, or have permissions to run wpa_cli and wpa_passphrase 
as root with sudo.
===============================================================================
"""             
class WpaManager(PiCommander):
    def __init__(self, **kwargs):
        super(WpaManager, self).__init__(**kwargs)
        self.sudo = False
        self.wpa_cli = '/sbin/wpa_cli'
        self.wpa_passphrase = '/sbin/wpa_passphrase'
        
        allowed = ['sudo', 'wpa_cli', 'wpa_passphrase']
        for k, v in kwargs.items():
            if k in allowed:
                setattr(self, k, v)
    
    
    """
    list networks in wpa_supplicant
    
    params:
        None
    returns:
        a list: [[index, ssid, bsid, flags], [etc...] ]
    """
    def list_networks(self):
        mylist = []
        cmd = [self.wpa_cli, 'list_networks']
        rval, out, err = self.run_command(cmd, self.sudo)
        for line in out.decode('utf-8').splitlines():            
            if not re.search(r'^\d+', line):
                # skip lines not starting with an index number
                continue
    
            id, ssid, bsid, flags = line.split("\t")
            if bsid:
                bsid = bsid.strip()
                
            if flags:
                flags = flags.strip()
                
            mylist.append([int(id.strip()), ssid.strip(), bsid, flags])
            
        return mylist
        
    
    """
    add new network to the wpa_supplicant.
    dict keys and values should match exactly the wpa_supplicant network
    fields you want to add.
    
    params:
        a dict containing wpa network settings
        { 'ssid': 'Foo', 'psk': "mypassword", 'scan_ssid': '1' }
    returns:
        0 on success, non-zero on failure
    """           
    def add_network(self, n):
        failures = 0
        idx = self.new_network_index()
        if idx is None:
            # really, is this the best I could do?
            # let's put a proper Exception here at some point, ok?
            raise
                    
        for k, v in n.items():    
            if self.set_network(idx, k, v):
                failures += 1
                # oops! something went wrong. don't leave partial networks
                # in the system. Delete it!
                # Exceptions, or error msgs, would be good here.
                failures += self.remove_network(idx)
                break    
        
        if not failures:
            if self.enable_network(idx):
                failures += 1
            else:
                if self.save_config():
                    failures += 1
    
        return failures
     
    
    """
    UNTESTED AND PROBABLY NOT WORKING AS IT SHOULD!!!
    
    edit network in the wpa_supplicant
    
    params:
        - a network index number
        - a dict containing wpa network settings
            { 'ssid': 'Foo', 'psk': "mypassword", 'scan_ssid': 1 }
    returns:
        0 on success, non-zero on failure
    """           
    def edit_network(self, idx, n):
        failures = 0            
        for k, v in n.items():
            if k == 'psk':
                # convert plain text password to a wpa passphrase instead
                v = self.passphrase(v)
                
            rval = self.set_network(idx, k, v)
            if rval:
                # messages here?
                failures += 1
                    
        return failures
        

    """
    Set network parameters
    params:
        - network index
        - parameter
        - setting
    returns:
        exit-code (0 = success)
    """
    def set_network(self, idx, key, val):
        quoted = ['ssid', 'psk', 'identity', 'ca_cert', 'client_cert',
                    'private_key', 'private_key_passwd', 'password',
                    'anonymous_identity']
                    
        if key in quoted:
            val = '"%s"' % str(val)
        else:
            val = str(val)  
            
        cmd = [self.wpa_cli, 'set_network', str(idx), key, val]
        rval, out, err = self.run_command(cmd, self.sudo)
        return rval


    """
    Remove a network from wpa_supplicant
    params:
        - network index number
    returns:
        exit-code (0 = success)
    """
    def remove_network(self, idx):
        cmd = [self.wpa_cli, 'remove_network', str(idx)]
        rval, out, err = self.run_command(cmd, self.sudo)
        return rval


    """
    write wpa_supplicant network info to the config file
    params:
        None
    returns:
        0 on success, non-zero on failure
    """
    def save_config(self):
        cmd = [self.wpa_cli, 'save_config']
        rval, out, err = self.run_command(cmd, self.sudo)
        return rval
        
    
    """
    enable a network
    
    params:
        - a network index number
    returns:
        0 on success, non-zero on failure
    """           
    def enable_network(self, idx):
        cmd = [self.wpa_cli, "enable_network", str(idx)]          
        rval, out, err = self.run_command(cmd, self.sudo)
        return rval
        
          
    """
    get a passphrase from wpa_passphrase, based on a string password
    """
    def passphrase(self, passwd):
        cmd = [self.wpa_passphrase, 'Foo', passwd]
        rval, out, err = self.run_command(cmd, self.sudo)
        for line in out.decode('utf-8').splitlines():
            if re.search(r'^\s*(#|$)', line):
                continue
            
            match = re.search(r'psk=(.+)', line)
            if match:
                return match.group(1)
    
        return None
    
    
    """
    Get new index number for network to be added
    """
    def new_network_index(self):
        cmd = [self.wpa_cli, "add_network"] 
        rval, out, err = self.run_command(cmd, self.sudo)
        for line in out.decode('utf-8').splitlines():
            match = re.search(r'^\s*(\d+)\s*$', line)
            if match:
                return int(match.group(1))
    
        return None
        
    
        