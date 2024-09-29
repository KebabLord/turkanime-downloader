"""
create_webdriver() -> driver
  - seleniumu hazırlar ve driver objesini döndürür.

find_firefox_executable() -> path:str
  - bilinen dizinlerde firefox binary'sini arar
"""

from os import name,path,getlogin,devnull
from time import time
import logging
from distutils import spawn
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import SessionNotCreatedException, NoSuchElementException
from selenium.webdriver.common.by import By

# Gereksiz uyarıları gizle
logging.basicConfig(level=logging.ERROR)

# Gerekli çerez & dosyaların yüklendiği dull sayfa
INIT_URL = "https://turkanime.co/kullanici/anonim"

def find_firefox_executable():
    """ chrome.exe'yi bilinen konumlarda ara. """
    possible_locations = [
        "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
        "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe",
        "C:\\Program Files\\Firefox Developer Edition\\firefox.exe",
        f"C:\\Users\\{getlogin()}\\AppData\\Local\\Mozilla Firefox\\firefox.exe"
        "/Applications/Firefox.app/Contents/MacOS/firefox",
        "/usr/bin/firefox",
        "/usr/local/bin/firefox",
        "/usr/bin/firefox-esr",
        "/usr/local/bin/firefox-esr",
        "/Applications/Firefox.app/Contents/MacOS/firefox",
        "/Applications/Firefox Developer Edition.app/Contents/MacOS/firefox",
    ]
    for location in possible_locations:
        if path.exists(location):
            return location
    raise SessionNotCreatedException("chrome'un konumu bulunamadı.")


def create_webdriver(options=None,headless=True,firefox_path=None,preload_ta=True):
    """ Selenium webdriver'ı hazırla. """
    if not options:
        options = Options()
    if headless:
        options.add_argument('--headless')
    if firefox_path:
        options.binary_location = firefox_path
    elif not spawn.find_executable("firefox"):
        options.binary_location = find_firefox_executable()
    # Pürüzsüz çalışması için profile tweaks.
    profile = webdriver.FirefoxProfile()
    profile.set_preference("app.update.auto", False)
    profile.set_preference("dom.webdriver.enabled", False)
    profile.set_preference('useAutomationExtension', False)
    profile.set_preference('permissions.default.image', 2)
    profile.set_preference("network.proxy.type", 0)
    profile.update_preferences()
    options.profile = profile
    try:
        service = Service(log_output=devnull)
    except TypeError:
        service = Service(log_path=devnull)
    if name == 'nt':
        driver = webdriver.Firefox(options=options, service=service)
    else:
        driver = webdriver.Firefox(options=options, service=service)
    if preload_ta:
        driver.get(INIT_URL)
    return driver


def elementi_bekle(selector,_driver):
    """ Element yüklenene dek bekler. Eğer 10 saniye
        boyunca yanıt alamazsa error verir.
    """
    start=round(time())
    while round(time())-start<10:
        try:
            _driver.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            continue
        break
    else:
        raise ConnectionError("TürkAnime'ye ulaşılamıyor")
