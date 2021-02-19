from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def init(driver_path="C:\\Program Files\\Google\\Chrome\\Application\\chromedriver.exe"):
    driver = webdriver.Chrome(driver_path)
    wait = WebDriverWait(driver, 10)
    return driver, wait