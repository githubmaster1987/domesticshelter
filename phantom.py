from scrapex import *
import time
import sys
import json
import urlparse
import re
from datetime import datetime
from datetime import date
from time import sleep
from scrapex import common
from scrapex.node import Node
from scrapex.excellib import *
import random
from time import sleep
import sys
import json
import csv
import random
from proxy_list import random_luminati_proxy
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common import exceptions as EX
from selenium.common.exceptions import ElementNotVisibleException
from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains

s = Scraper(
	use_cache=False, #enable cache globally
	retries=2,
	delay=0.5,
	timeout=240,
	proxy_file = 'proxy.txt',
	proxy_auth= 'silicons:1pRnQcg87F'
	)
luminati_zone_proxy_username = "lum-customer-hl_1dafde3b-zone-zone1"
luminati_zone_proxy_pwd = "n9ndhce734x9"

luminati_proxy_host = "zproxy.luminati.io"
luminati_proxy_port = 22225


logger = s.logger

city_file = "city.csv"
geo_file = "city_geo.csv"
list_file = "list.csv"

start_url = "https://www.domesticshelters.org/"
city_url = "http://www.craigslist.org/about/sites#US"
item_list_file = "list.csv"

DRIVER_WAITING_SECONDS = 60
DRIVER_MEDIUM_WAITING_SECONDS = 10
DRIVER_SHORT_WAITING_SECONDS = 3

MOBILE_SC = [[480,800], [240,320], [800,480], [800,1280], [720,1280], [1920,1080], [2560,1440], [1440,2560], [1280,720], [960,540], [480,360], [1334,750], [640,1136], [960,640], [480,320]]
TABLET_SC = [[1280,800], [1024,600], [1024,768], [2048,1536], [2732,2048], [768,1024], [768,1280]]
DESKTOP_SC = [[1920,1080], [1600,900], [1280,1024], [1152,864], [1024,768], [800,600]]


class AnyEc:
	""" Use with WebDriverWait to combine expected_conditions
		in an OR.
	"""
	def __init__(self, *args):
		self.ecs = args
	def __call__(self, driver):
		for fn in self.ecs:
			try:
				if fn(driver): return True
			except:
				pass

def create_phantomjs_driver(c_type='http', ua=None, proxy=None, screen_resolution=None):
    if ua == None:
        ua = ["D", "W", "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:53.0) Gecko/20100101 Firefox/53.0"]
        # e.g. ["M", "A", "Mozilla/5.0 (Android; Mobile; rv:40.0) Gecko/40.0 Firefox/40.0"],
        if ua[0] == "M": # Mobile
            screen_resolution = random.choice(MOBILE_SC)
        elif ua[0] == "T": # Tablet
            screen_resolution = random.choice(TABLET_SC)
        else: # elif ua[0] == "D": # Desktop
            screen_resolution = random.choice(DESKTOP_SC)

    proxy_ip = random_luminati_proxy()
    #proxy_ip = "173.245.85.243:29842"

    dcap = dict(DesiredCapabilities.PHANTOMJS)
    #dcap["phantomjs.page.settings.userAgent"] = ua[2]
    dcap['phantomjs.page.settings.loadImages'] = True
    dcap['phantomjs.page.settings.resourceTimeout'] = 60000

    #dcap['phantomjs.page.customHeaders.User-Agent'] = ua[2]
#    dcap['phantomjs.page.customHeaders.Accept'] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    #dcap['phantomjs.page.customHeaders.Accept-Encoding'] = "gzip, deflate, sdch, br"
    
    accept_language = "en-US,en;q=0.8"
   
    if accept_language != "":
       dcap['phantomjs.page.customHeaders.Accept-Language'] = accept_language
    
    # Proxy Provider proxy
    # auth_str = "%s:%s" % ("lether", "C6zG2Dyh")
    # service_args = ['--proxy=%s' % proxy_ip, '--proxy-type=%s' % c_type,'--proxy-auth=%s' % auth_str , '--ignore-ssl-errors=true', '--ssl-protocol=any'] 

    #Luminati Proxy Service
    proxy_str = "{}:{}".format(luminati_proxy_host, luminati_proxy_port)

    auth_str = "{}-ip-{}:{}".format(luminati_zone_proxy_username, proxy_ip, luminati_zone_proxy_pwd)
    service_args = ['--proxy=%s' % proxy_str, '--proxy-type=%s' % c_type,'--proxy-auth=%s' % auth_str , '--ignore-ssl-errors=true', '--ssl-protocol=any'] 

    # print('user-agent -> ' + ua[2])
    # print('proxy -> %s %s, language -> %s' % (proxy_ip, auth_str, accept_language))
    # print('screen resolution -> %d x %d' % (screen_resolution[0], screen_resolution[1]))
    # print (service_args)
    try:
        driver = webdriver.PhantomJS(desired_capabilities=dcap, service_args=service_args)
        #driver = webdriver.PhantomJS()
    except WebDriverException as e:
        print("webdriver.PhantomJS WebDriverException -> %s" % str(e))
        try:
            phantom_Quit(driver)
        except:
            pass
        return None, ua, proxy, screen_resolution

    driver.set_window_size(screen_resolution[0], screen_resolution[1])
    driver.implicitly_wait(DRIVER_WAITING_SECONDS)
    driver.set_page_load_timeout(DRIVER_WAITING_SECONDS)

    return driver, ua, proxy_ip, screen_resolution

def get_geolocation():
	with open(city_file) as csvfile:
		reader = csv.reader(csvfile)
		for i, item in enumerate(reader):
			if i > 0:
				city_str = item[0]

				json_obj = s.load_json("https://maps.googleapis.com/maps/api/geocode/json?address={}&key=AIzaSyBBJbYJoYNH3edgpio4MSliiMWgTxu4yjs".format(city_str))
				lat = ""
				lng = ""

				try:
					lat = json_obj["results"][0]["geometry"]["location"]["lat"]
					lng = json_obj["results"][0]["geometry"]["location"]["lng"]
					print city_str, json_obj["results"][0]["geometry"]["location"]
				except:
					lat = ""
					lng = ""

				item = [
					"city", city_str,
					"latitude", lat,
					"longitude", lng,
				]	
				s.save(item, geo_file)
	

def get_city_info():
	html = s.load(city_url, use_cache = False)
	
	proxy = html.response.request.get("proxy")
	logger.info(proxy.host + ":" + str(proxy.port))

	city_divs = html.q("//div[@class='colmask']/div/ul/li/a")
	logger.info(len(city_divs))

	for city in city_divs:
		city_str = city.x("text()").strip()

		item = [
			"city", city_str,
		]	
		s.save(item, city_file)
	return

def get_start_urls():
	with open(city_file) as csvfile:
		reader = csv.reader(csvfile)
		for i, item in enumerate(reader):
			if i > 0:
				url = start_url + "search#?q={}&latitude={}&longitude={}&radius=50"
				html = s.load_html(url, use_cache = False)
				
				with open("response.html", 'w') as f:
					f.write(html.encode('utf-8'))

				return
	for url in group_urls:
		logger.info('loading parent page...' + url)
		html = s.load(url, use_cache = False)

		proxy = html.response.request.get("proxy")
		logger.info(proxy.host + ":" + str(proxy.port))
	
		video_divs = html.q("//h3[@class='yt-lockup-title ']/a")
	
		href_links = []
		if len(video_divs) > 0:
			for row in video_divs:
				url_obj = {}
				url_obj["url"] = row.x("@href")
				url_obj["group_url"] = url
				url_lists.append(url_obj)

	for url in individual_urls:
		url_obj = {}
		url_obj["url"] = url
		url_obj["group_url"] = ""
		url_lists.append(url_obj)
	
	for url in url_lists:
		item = [
			"url", url["url"],
			"group_url", url["group_url"],
		]	
		s.save(item, url_file)

def create_proxyauth_extension(proxy_host, proxy_port,
							   proxy_username, proxy_password,
							   scheme='http', plugin_path=None):
	"""Proxy Auth Extension

	args:
		proxy_host (str): domain or ip address, ie proxy.domain.com
		proxy_port (int): port
		proxy_username (str): auth username
		proxy_password (str): auth password
	kwargs:
		scheme (str): proxy scheme, default http
		plugin_path (str): absolute path of the extension       

	return str -> plugin_path
	"""
	import string
	import zipfile

	if plugin_path is None:
		plugin_path = '/tmp/vimm_chrome_proxyauth_plugin.zip'

	manifest_json = """
	{
		"version": "1.0.0",
		"manifest_version": 2,
		"name": "Chrome Proxy",
		"permissions": [
			"proxy",
			"tabs",
			"unlimitedStorage",
			"storage",
			"<all_urls>",
			"webRequest",
			"webRequestBlocking"
		],
		"background": {
			"scripts": ["background.js"]
		},
		"minimum_chrome_version":"22.0.0"
	}
	"""

	background_js = string.Template(
	"""
	var config = {
			mode: "fixed_servers",
			rules: {
			  singleProxy: {
				scheme: "${scheme}",
				host: "${host}",
				port: parseInt(${port})
			  },
			  bypassList: ["foobar.com"]
			}
		  };

	chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

	function callbackFn(details) {
		return {
			authCredentials: {
				username: "${username}",
				password: "${password}"
			}
		};
	}

	chrome.webRequest.onAuthRequired.addListener(
				callbackFn,
				{urls: ["<all_urls>"]},
				['blocking']
	);
	"""
	).substitute(
		host=proxy_host,
		port=proxy_port,
		username=proxy_username,
		password=proxy_password,
		scheme=scheme,
	)

	with zipfile.ZipFile(plugin_path, 'w') as zp:
		zp.writestr("manifest.json", manifest_json)
		zp.writestr("background.js", background_js)

	return plugin_path

def start_selenium():
	url_lists = []
	with open(geo_file) as csvfile:
		reader = csv.reader(csvfile)
		for i, item in enumerate(reader):
			if i > 0:
				url = start_url + "search#?q={}&latitude={}&longitude={}&radius=50&page=1".format(item[0], item[1], item[2])
				url_lists.append(url)

	luminati_zone_proxy_username = "lum-customer-hl_1dafde3b-zone-zone1"
	luminati_zone_proxy_pwd = "n9ndhce734x9"

	luminati_proxy_host = "zproxy.luminati.io"
	luminati_proxy_port = 22225

	for ind, url in enumerate(url_lists):
		if ind < 50:
			continue

		logger.info("Index-------------------- -> {}".format(ind))

		# proxy_ip = random_luminati_proxy()
		# proxy_str = "{}:{}".format(luminati_proxy_host, luminati_proxy_port)
		# auth_str = "{}-ip-{}".format(luminati_zone_proxy_username, proxy_ip, )
		
		# proxyauth_plugin_path = create_proxyauth_extension(
		# 		proxy_host=luminati_proxy_host,
		# 		proxy_port=luminati_proxy_port,
		# 		proxy_username=auth_str,
		# 		proxy_password=luminati_zone_proxy_pwd
		# 	)
				
		# co = Options()
		# co.add_argument("--start-maximized")
		# co.add_extension(proxyauth_plugin_path)
		# driver = webdriver.Chrome(chrome_options=co)

		driver, user_agent, proxy, screen_resolution = create_phantomjs_driver()       #PHANTOMJS PART

		sleep(random.randrange(DRIVER_MEDIUM_WAITING_SECONDS))

		driver.get(url)
		logger.info(url)
		while(1):
			# try:
			sleep(random.randrange(DRIVER_MEDIUM_WAITING_SECONDS))
			logger.info("Wait page loading")
			driver.save_screenshot("a.png")
			pagination_container = WebDriverWait(driver, DRIVER_WAITING_SECONDS).until(AnyEc
				(
					EC.presence_of_element_located(
						(By.XPATH, "//div[@id='box1 d-pad-30']")
					),
					EC.presence_of_element_located(
						(By.XPATH, "//div[@class='unable-to-find']")
					),
				)
			)

			logger.info("Page is loaded")

			try:
				unabel_find = driver.find_element_by_xpath("//div[@class='unable-to-find']")
			except Exception as e:
				logger.info(e)

			doc = Doc(html=driver.page_source)
			divs = doc.q("//li[@class='box1 d-pad-30']")
			logger.info(len(divs))
			for div in divs:
				href = div.x("h2/a/@href").strip()
				item = [
					"url", href,
					"parent", url.replace("&page=1", ""),
					"ind", ind
				]
				s.save(item, list_file)
				logger.info(href)

			logger.info ("Next Button")
			driver.save_screenshot("b.jpg")
			next_button = driver.find_element_by_xpath('//a[contains(@class,"next_page")]')
			driver.execute_script('window.scrollTo(' + str(next_button.location['x']) + ', ' + str(next_button.location['y']) + ');')
			
			sleep(random.randrange(DRIVER_SHORT_WAITING_SECONDS))
			next_button.click()
			sleep(random.randrange(DRIVER_MEDIUM_WAITING_SECONDS))
			# except:
			# 	break
		
		driver.quit()
		break
		
if __name__ == '__main__':
	
	#get_city_info()
	#get_geolocation()
	#get_start_urls()
	start_selenium()
