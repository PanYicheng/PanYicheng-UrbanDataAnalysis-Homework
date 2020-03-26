from selenium import webdriver
browser = webdriver.Chrome()
print(browser.get_network_conditions())
browser.quit()