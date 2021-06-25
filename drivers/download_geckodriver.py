#!/usr/local/bin/python3
import sys
import os
import struct
import requests
from bs4 import BeautifulSoup

session = requests.Session()
r = session.get("https://github.com/mozilla/geckodriver/releases")
s = BeautifulSoup(r.text,'html.parser')

latest_version = s.find('div',{'class':'release-header'}).find('a').text
base_url = r.url[:r.url.find('/mozilla')]
releases = s.find('div', {'class': 'Box Box--condensed mt-3'})
links = releases.findAll('a',{'class':'d-flex flex-items-center min-width-0'})
links = list(map(lambda x: base_url+x.get('href'), links))

mac_links = list(filter(lambda x: 'mac' in x, links))
windows_links = list(filter(lambda x: 'win' in x, links))
linux_links = list(filter(lambda x : 'linux' in x,links))

download_links = {
    'linux': dict(zip([32, 64], linux_links)),
    'win32': dict(zip([32, 64], windows_links)),
    'darwin': mac_links[1]
}    
   
#this_os = 'linux' if sys.platform.startswith('linux') else sys.platform
this_os = 'darwin'
this_os_architecture = struct.calcsize("P") * 8
try:
    download_url = download_links[this_os].get(this_os_architecture)
except AttributeError:
    download_url = download_links[this_os]

extension = download_url[ download_url.rfind('.') :  ].replace('.gz','.tar.gz')
fname = 'geckodriver' + latest_version + extension

print(f"Your OS type : {this_os}\nYour OS architecture : {this_os_architecture}\nFile being downloaded:{fname}\n\nFile download URL : {download_url}\n")

try:
    if input("\nContinue? [Y/n]: ").lower() == 'y':
        f = session.get(download_url)
        open(fname,'wb+').write(f.content)
        
        if this_os == 'linux':
            print("File downloaded succesfully in linux directory...")
            os.system(f"tar -xvf {fname} && rm gecko*.gz && chmod +x geckodriver && mv geckodriver linux/")
            print("\nAll done! Now you can run selenium scripts without a worry!")
        elif this_os == 'darwin':
            print("File downloaded succesfully in mac directory...")
            os.system(f"tar -xvf {fname} && rm gecko*.gz && chmod +x geckodriver && mv geckodriver mac/")
            print("\nAll done! Now you can run selenium scripts without a worry!")
        else:
            print("File downloaded successfully! Extract the binary from the archive and move the file to 'windows' directory.")
    else:
        print("Download aborted !!!")
finally:
    session.close()
    sys.exit()
