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
import sys
import csv
import random
from proxy_list import random_luminati_proxy

s = Scraper(
	use_cache=False, #enable cache globally
	retries=2,
	delay=0.5,
	timeout=240,
	proxy_file = 'proxy.txt',
	proxy_auth= 'silicons:1pRnQcg87F'
	)

DRIVER_WAITING_SECONDS = 60
DRIVER_MEDIUM_WAITING_SECONDS = 10
DRIVER_SHORT_WAITING_SECONDS = 3

logger = s.logger

url_file = "urls.csv"

group_urls = [
	'https://www.youtube.com/user/CommercialAppraisers/videos',
	'https://www.youtube.com/user/PacificAppraisers/videos',
	'https://www.youtube.com/user/njpropertyappraiser/videos',
	'https://www.youtube.com/user/IRRSanDiegoAppraiser/videos',
	'https://www.youtube.com/channel/UCRQkRpHyP7VbFp2-eX1mK2Q',
	'https://www.youtube.com/channel/UCwGnRooW-wA_U-pFeQOsPYA',
]

individual_urls = [
	'https://www.youtube.com/watch?v=IrQk_oL7nnM&list=WL&index=157',
	'https://www.youtube.com/watch?v=MP4viH08Hl0',
	'https://www.youtube.com/watch?v=cJDXNoSIS6s',
	'https://www.youtube.com/watch?v=wqNnb1SZOho',
	'https://www.youtube.com/watch?v=KPXaqJvQadk',
	'https://www.youtube.com/watch?v=07zwWGF3XA8',
	'https://www.youtube.com/watch?v=qIPPKofrhdU&t=3s',
	'https://www.youtube.com/watch?v=1v6NeSuPtoY',
	'https://www.youtube.com/watch?v=zAzyx8K1oYk&t=4s',
	'https://www.youtube.com/watch?v=ZgRUPJpOxlU',
	'https://www.youtube.com/watch?v=valWBwj62uo',
]

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


def get_start_urls():
	url_lists = []
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
	with open(url_file) as csvfile:
		reader = csv.reader(csvfile)
		print ( "-----------------CSV Read------------------" )
		i = 0
		for input_item in reader:
			if i > 0:
				url = {}
				url["url"] = input_item[0]
				url["group_url"] = input_item[1]
				url_lists.append(url)
			i+=1

	luminati_zone_proxy_username = "lum-customer-hl_1dafde3b-zone-zone1"
	luminati_zone_proxy_pwd = "n9ndhce734x9"

	luminati_proxy_host = "zproxy.luminati.io"
	luminati_proxy_port = 22225

	#for url in url_lists:
	url = random.choice(url_lists)
	proxy_ip = random_luminati_proxy()
	proxy_str = "{}:{}".format(luminati_proxy_host, luminati_proxy_port)
	auth_str = "{}-ip-{}".format(luminati_zone_proxy_username, proxy_ip, )
	
	proxyauth_plugin_path = create_proxyauth_extension(
			proxy_host=luminati_proxy_host,
			proxy_port=luminati_proxy_port,
			proxy_username=auth_str,
			proxy_password=luminati_zone_proxy_pwd
		)

	co = Options()
	co.add_argument("--start-maximized")
	#co.add_extension(proxyauth_plugin_path)
	driver = webdriver.Chrome(chrome_options=co)
	
	driver.get(url["url"])
	sleep(random.randrange(DRIVER_WAITING_SECONDS))

	more_span = WebDriverWait(driver, DRIVER_WAITING_SECONDS).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='yt-uix-menu ']/button[contains(@class, 'yt-uix-tooltip')]")))

	logger.info("Page is loading->")
	more_span = WebDriverWait(driver, DRIVER_WAITING_SECONDS).until(EC.presence_of_element_located((By.XPATH, "html")))
	sleep(random.randrange(DRIVER_SHORT_WAITING_SECONDS))
	logger.info("Wait More->")
	WebDriverWait(driver, DRIVER_WAITING_SECONDS).until(EC.presence_of_element_located((By.XPATH, "//div[@class='yt-uix-menu ']/button[contains(@class, 'yt-uix-tooltip')]")))
	sleep(random.randrange(DRIVER_SHORT_WAITING_SECONDS))
	
	retry_flg = True
	while(retry_flg == True):
		try:	
			more_span = driver.find_element_by_xpath("//div[@class='yt-uix-menu ']/button[contains(@class, 'yt-uix-tooltip')]")
			logger.info("Found More->")
			more_span.click()
			logger.info("More Clicked->")
			sleep(random.randrange(DRIVER_SHORT_WAITING_SECONDS))


			logger.info("Wait Transcript->")
			transcript = WebDriverWait(driver, DRIVER_WAITING_SECONDS).until(EC.presence_of_element_located((By.XPATH, "//li/button[contains(@class, 'action-panel-trigger-transcript')]")))
			logger.info("Found Transcript->")
			sleep(random.randrange(DRIVER_SHORT_WAITING_SECONDS))

			transcript.click()
			logger.info("Transcript Clicked->")
			sleep(random.randrange(DRIVER_SHORT_WAITING_SECONDS))

			logger.info("Transcript Queue Waiting->")
			transcript = WebDriverWait(driver, DRIVER_WAITING_SECONDS).until(EC.presence_of_element_located((By.XPATH, "//div[@class='caption-line']")))
			logger.info("Transcript Queue Founded->")
			sleep(random.randrange(DRIVER_MEDIUM_WAITING_SECONDS))

			logger.info("Transcript Wait->")
			transcript = WebDriverWait(driver, DRIVER_WAITING_SECONDS).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='caption-line']")))
			logger.info("Transcript Load->")
			sleep(random.randrange(DRIVER_MEDIUM_WAITING_SECONDS))

			doc = Doc(html= driver.page_source)
			divs = doc.q("div[contains(@class,'caption-line')]")	
			logger.info(len(divs))
			retry_flg =  False

		except ElementNotVisibleException as e:
			logger.info(e)
			retry_flg = True

	for div in divs:
		time_str = div.x("div[@class='caption-line-time']/text()").strip()
		text_str = div.x("div[@class='caption-line-text']/text()").strip()
		logger.info("{}, {}".format(time_str, text_str))
	#driver.quit()
	sleep(random.randrange(DRIVER_WAITING_SECONDS))
	return

if __name__ == '__main__':
	#get_start_urls()
	start_selenium()
