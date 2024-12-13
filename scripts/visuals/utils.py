import os
from selenium import webdriver
import time
import folium

def save_folium_map(m, save_path):
    delay=2
    fn='temp_map.html'
    tmpurl='file://{path}/{mapfile}'.format(path=os.getcwd(),mapfile=fn)
    m.save(fn)

    browser = webdriver.Firefox()
    browser.get(tmpurl)
    browser.set_window_size(1920, 1432)
    time.sleep(delay)
    browser.save_screenshot(save_path)
    browser.quit()
    os.remove(fn)