#!/usr/local/bin/python3
import selenium
import time
import string
import sys
import os
import re
import random
import requests
import qrcode
import pyfiglet
import argparse
from colorama import init as colorama_init, Fore
from subprocess import run,PIPE
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from msedge.selenium_tools import Edge, EdgeOptions
from selenium.webdriver.firefox.options import Options as FireOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# global variables
browser = None
rep = 0

#  Start working in background while waiting for user input
def initialize():
    b = args.browser.lower()
    d = args.debug
    global browser

    print("\n\aConnecting to Saavn...\n")
    driver_dir = os.path.dirname(os.path.realpath(__file__))
    if b == 'firefox':
        opt = FireOptions()
        opt.headless = True

        if sys.platform.startswith('linux'):
            path = os.path.join(driver_dir,'drivers','linux','geckodriver')
        elif sys.platform == 'darwin':
            path = os.path.join(driver_dir, 'drivers', 'mac', 'geckodriver')
        else:
            path = os.path.join(driver_dir,'drivers','windows','geckodriver.exe')

        try:
            if d == 'on':
                print("Debugging mode turned ON...")
                browser = webdriver.Firefox(executable_path=path,service_log_path=os.path.devnull)
            else:
                raise IndexError
        except IndexError:
            browser = webdriver.Firefox(executable_path=path,options=opt,service_log_path=os.path.devnull)
    elif b == 'chrome':
        opt = ChromeOptions()
        opt.add_argument("--log-level=3")
        opt.add_argument("--window-size=1366,768")

        if d == 'on':
            print("Debugging mode turned ON...")
        else:
            opt.add_argument("--headless")

        if sys.platform == 'linux':
            path = os.path.join(driver_dir,'drivers','linux','chromedriver')
        elif sys.platform == 'darwin':
            path = os.path.join(driver_dir, 'drivers', 'mac', 'chromedriver')
        else:
            path = os.path.join(driver_dir,'drivers','windows','chromedriver.exe')
    
        browser = webdriver.Chrome(executable_path=path,options=opt,service_log_path=os.path.devnull)
    elif b == 'edge':
        opt = EdgeOptions()
        opt.use_chromium = True

        opt.add_argument("--log-level=3")
        opt.add_argument("--window-size=1366,768")
        del opt.capabilities['platform']

        if d == 'on':
            print("Debugging mode turned ON...")
        else:
            opt.add_argument('--headless')

        if sys.platform == 'linux':
            path = os.path.join(driver_dir,'drivers','linux','msedgedriver')
        elif sys.platform == 'darwin':
            path = os.path.join(driver_dir, 'drivers', 'mac', 'msedgedriver')
        else:
            path = os.path.join(driver_dir,'drivers','windows','msedgedriver.exe')
        
        browser = Edge(executable_path=path, options=opt, service_log_path=os.path.devnull)
        
    return True

# fetch name of song as input from user
def get_song_name():
    song_name = ''

    while song_name == '':
        song_name = '+'.join(input("Enter the song name you want to listen to....\n> ").split())

    return song_name

# backdoor entry for debugging purposes
def debug(*args,**kwargs):
    while(True):
        try:
            cmd = input("Enter the debugging commands...\n")
            if cmd == 'exit' or cmd == '':
                return
            exec(cmd)
        except:
            print('\nBAD CODE\n')
            pass

# wait for element to be clickable with 20 seconds as limit
def wait_and_find(element,selector,root=browser):
    try:
        WebDriverWait(browser,20).until(EC.element_to_be_clickable((selector,element)))
    except TimeoutException as e:
        print("Something went wrong",e,'\n',element)
    
    return root.find_elements(selector,element)

# fixes a bug in Saavn website which resets volume to 32% after each song
def check_volume():
    if browser.execute_script('return MUSIC_PLAYER.getVolume()') != 100:
        browser.execute_script("MUSIC_PLAYER.setVolume(100);")

def fix_volume_bug():
    try:
        while(browser.title):
            check_volume()
            time.sleep(10)
    except:
        pass

# search for a new song
def new_song():
    print("Enter 'q' to cancel")
    song_name = get_song_name()
    
    if song_name == 'q':
        pass
    else:
        navigate(song_name)

# play next song
def next_song():
    fwd = browser.find_element_by_class_name('c-player__btn-next').find_element_by_tag_name('span')
    browser.execute_script('arguments[0].click()',fwd)
    print("\nPlaying next song...\n")

# toggle play/pause
def play_pause():
    browser.execute_script('MUSIC_PLAYER.playToggle()')

# play next song
def prev_song():
    rew = browser.find_element_by_class_name('c-player__btn-prev').find_element_by_tag_name('span')
    browser.execute_script('arguments[0].click()',rew)
    print("\nPlaying the last song....\n")

# get current track details
def info(flush=False):
    track_name = browser.find_element_by_xpath("//h4[@class='u-deci u-ellipsis u-margin-bottom-none@sm']").text
    meta_name = browser.find_element_by_xpath("//p[@class='u-centi u-ellipsis u-color-js-gray-alt-light u-margin-bottom-none@sm']").text
    duration = browser.find_element_by_xpath("//span[@class='u-centi u-valign-text-bottom u-padding-horizontal-small@sm']").text

    if not flush:
        print("\nTrack name : "+track_name+' from the artist/album -  '+meta_name)
        print("\nTrack duration : "+duration)

    return track_name,meta_name,duration

# repeat current song
def repeat():
    global rep

    rep_button = browser.find_element_by_xpath("//li[@class='c-player__btn c-player__btn--shift c-player__btn-action1']").find_element_by_tag_name('span')

    if rep == 0:
        rep = 1
        browser.execute_script('arguments[0].click();', rep_button)
        print('\nRepeat mode ON\n')
    elif rep == 1:
        rep = 0
        for _ in range(0,2):
            browser.execute_script('arguments[0].click();', rep_button)
            time.sleep(0.3)
        print('\nRepeat mode OFF\n')

# display lyrics for current song
def lyrics():
    name = info(True)[0]

    if input("The current search paramter is '{}'. Do you want to continue ('n') or refine it? ('y')\n> ".format(name)) == 'y':
        name = input("Enter the search term...\n> ")
        print("Okay... Searching for {}...".format(name))
    else:
        print("Searching for {}...".format(name))

    r = requests.get("https://search.azlyrics.com/search.php?q="+'+'.join(name.split()),headers={'User-Agent':'MyApp'})
    s = BeautifulSoup(r.text,'html.parser')
    td = s.findAll('td',attrs={'class':'text-left visitedlyr'})
    res = []

    if len(td) == 0:
        custom = input("No results found for this...Want to try again? (y)\n")
        if custom =='y':
            lyrics()
        else:
            print('\nOkay... returning to main menu...\n')
        return

    for i,j in enumerate(td):
        s=re.findall(r'<b>.*</b>',str(j))[0]
        for r in (('<b>',''),('</b>',''),('</a>','')):
            s=s.replace(*r)
        print(i,s)
        res.append(j.find('a').get('href'))

    choice = input("\nChoose one from above : (type 'exit' to go back to previous menu)\n")

    for i,j in enumerate(res):
        if choice==str(i):
            q = requests.get(j,headers={'user-agent':'MyApp'})
            s = BeautifulSoup(q.text,'html.parser')
            l = s.find('div',attrs={'class':'col-xs-12 col-lg-8 text-center'})
            try:
                print(l.find('div',attrs={'class':''}).text)
            except AttributeError:
                print('\nOops! Requested lyrics not available...\n')
        elif choice == 'exit':
            return

# download songs using youtube-dl, bit of an overkill but worth it
def download():
    search_term = info(True)[0]
    print("Fetching results for "+search_term)
    r = requests.get("http://youtube.com/results?search_query=" + '+'.join(search_term),headers={'User-Agent':'random_stuff'})

    print("Searching....")
    s = BeautifulSoup(r.text, 'html.parser')
    l = s.select('div .yt-lockup-content')

    urls = []
    titles = []

    try:
        for i in l:
            urls.append('http://youtube.com'+i.find('a').get('href'))
            titles.append(i.find('a').get('title'))
    except:
        pass

    length = len(l)
    if len(l) > 5:
        # show only 50% of results
        length = int(len(l)*0.50)   

    for i,t,u in zip(range(length),titles,urls):
        print('\n',i,t.upper(),'\nYouTube URL : ',u)

    ch = input("Choose from the above : ('exit' to go back)\n> ")

    for i,j in enumerate(urls):
        if ch==str(i):
            op = run("youtube-dl --extract-audio --audio-format mp3 "+j,shell=True,stderr=PIPE)
            error = op.stderr.decode('utf-8')
            if error != '':
                if 'ffprobe/avprobe' in error:
                    pass
            else:
                print(error)
        elif ch == 'exit':
            print("\nDownload aborted!")
            return

    print("Successfully Downloaded {}".format(search_term))
    return

# skip to preferred time, format - mm:ss
def seek():
    try:
        time = info(True)[2].split('/')
        max_time = time[1].strip()
        curr_time = time[0].strip()

        user_time = input("\nThe total duration of the track is : {}.\nThe current duration of the track is : {}. ( enter 'r' to refresh )\nEnter the new time in '[mm:ss]' format :\n> ".format(max_time,curr_time))

        if 'r' in user_time.lower():
            seek()

        try:
            total = list(map(int,max_time.split(':')))
            time = list(map(int,user_time.split(':')))
        except:
            raise Exception

        if time[0] > total[0] or (time[0] == total[0] and time[1] > total[1]):
            raise Exception

        time_in_secs = 60 * time[0] + time[1]

        browser.execute_script(f'MUSIC_PLAYER.seek({time_in_secs})')
        print('Song successfully skipped to '+user_time+"!\n")
    except Exception:
        print("\nWrong time or time format.. Try again...")
        return

# display QR code to share current song
def share():
    try:
        browser.find_element_by_xpath("//span[@class='o-icon-ellipsis o-icon--xlarge u-valign-bottom c-btn-overflow']").click()
    except selenium.common.exceptions.ElementClickInterceptedException:
        pass
    
    time.sleep(0.5)
    link = browser.execute_script("return document.getElementsByClassName('u-hidden-visually')[0].textContent")
    print("Share this link or scan the QR code :- {}".format(link))
    img = qrcode.make(link)
    img.show()

# wrap up
def cya():
    sys.exit('Stopping playback...Closing Saavn...')

# fall back for wrong user inputs
def default():
    print('Wrong Choice!\n')
    return

# ultimate browser controller
def handler():
    Thread(target=fix_volume_bug).start()
    try:
        routes = {'1':new_song,'2':next_song,'3':play_pause,'4':prev_song,'5' : seek,'6':info,'7':repeat,'8':lyrics,'9':download,'10':share,'11':cya,'12':debug,'default':default}

        while True:
            time.sleep(0.5)
            info()
            
            ch = input(f"\n'1' : New Song\n'2' : Next Song\n'3' : Play/Pause\n'4' : Previous Song\n'5' : Seek Song\n'6' : Song Info\n'7' : Repeat Current Song\n'8' : Lyrics for Current Song...\n'9' : Download current song...\n'10' : Share current song...\n'11' : Close Saavn\n\nEnter your choice...\n> ")

            if ch in routes:
                routes[ch]()
            else:
                routes['default']()

    except selenium.common.exceptions.ElementClickInterceptedException:
        browser.find_element_by_tag_name('html').send_keys(Keys.ESCAPE)
        print('\nPlease select again... Sorry for minor inconvenience\n')
        handler()

# navigating around saavn
def navigate(song_name,gui=False):
    # fallback in case of playback errors
    def restart(msg):
        print(msg)
        navigate(get_song_name())

    try:
        print("\nSearching for "+' '.join(song_name.split('+'))+'...')
        browser.get('https://jiosaavn.com/search/{}'.format(song_name))
        time.sleep(3)
    except:
        browser.quit()
        sys.exit('\nCheck your internet connection and try again...\n')

    # logic to start playback:
    titles = wait_and_find('u-color-js-gray',By.CLASS_NAME,browser)[1::2][:10]
    artists = browser.find_elements_by_xpath("//div[@class='o-snippet__item']//p[@class='u-centi u-ellipsis u-color-js-gray-alt-light u-margin-right@sm u-margin-right-none@lg']")[::2][:10]

    data = zip(list(range(len(titles))), titles, artists)

    if gui:
        print("Sending data...")
        return list(data)

    if len(titles) < 1:
        restart('No results found! Try again. If it still does not work, the UI must have been updated by Saavn.')

    for i,j,k in data:
            print(i+1,' : ',j.text,' : ',k.text)

    # accept cookies one time only:
    try:
        browser.find_element_by_css_selector("span[class='c-btn c-btn--senary c-btn--tiny']").click()
    except:
        pass

    # selects random track:
    # browser.execute_script("arguments[0].click()",random.choice(titles))

    ch = input("\nEnter your choice ('exit' to quit and 'q' to return):\n> ")
    for i,j in enumerate(titles,1):
        if ch == str(i):
            browser.execute_script("arguments[0].click();", j)
        elif ch == '':
            browser.execute_script("arguments[0].click();", titles[0])
        elif ch == 'exit':
            return
        elif ch == 'q':
            return

    time.sleep(3)
    # play_btn = browser.find_element_by_css_selector("a[class='c-btn c-btn--primary']")
    play_btn = wait_and_find("a[class='c-btn c-btn--primary']",By.CSS_SELECTOR,browser)[0]
    play_btn.click()
    time.sleep(2)
    
    # hack to check if song is playable
    try:
        browser.execute_script("MUSIC_PLAYER")
    except:
        restart('\nError while playing this song... Try another...\n')

    handler()

if __name__ == '__main__':
    # Colorama init function:
    colorama_init(autoreset=True)
    print(Fore.GREEN + pyfiglet.figlet_format('S A A V N  C L I'))

    parser = argparse.ArgumentParser(description="  Browser choice and debug mode")
    parser.add_argument("-b", "--browser", type=str, metavar='', required=True, help="firefox / chrome / edge")
    parser.add_argument("-d", "--debug", type=str, metavar='', required=True, help="on / off")
    args = parser.parse_args()

    try:
        init = Thread(target=initialize)
        init.start()
        
        song_name = get_song_name()
        
        #  if Python's too slow, wait for it ;)
        if init.is_alive():
            init.join()
        
        navigate(song_name)

    except Exception as e:
        print(e)
        
    finally:
        try:
            browser.quit()
        except:
            pass
        sys.exit("Thank you for using this software. Keep rockin' 🎵🤘🎵")
