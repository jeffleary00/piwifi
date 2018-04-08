from distutils.core import setup
setup(
  name = 'piwifi',
  packages = ['piwifi'],
  version = '0.1',
  description = 'Manage wpa_supplicant wifi networks on Raspberry Pi',
  author = 'Jeff Leary',
  author_email = 'sillymonkeysoftware@gmail.com',
  url = 'https://github.com/jeffleary00/piwifi',
  download_url = 'https://github.com/jeffleary00/piwifi/tarball/0.1',
  classifiers = [
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
  ],
  keywords = ['wpa_supplicant', 'raspberry pi', 'linux'], 
)