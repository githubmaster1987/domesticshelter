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
import threading

lock = threading.Lock()


s = Scraper(
	use_cache=False, #enable cache globally
	retries=2,
	delay=0.5,
	timeout=240,
	proxy_file = 'proxy.txt',
	proxy_auth= 'silicons:1pRnQcg87F'
	)

logger = s.logger

city_file = "city.csv"
geo_file = "city_geo.csv"
list_file = "list.csv"
detail_file = "result.csv"

start_url = "https://www.domesticshelters.org"
city_url = "http://www.craigslist.org/about/sites#US"
item_list_file = "list.csv"

DRIVER_WAITING_SECONDS = 60
DRIVER_MEDIUM_WAITING_SECONDS = 10
DRIVER_SHORT_WAITING_SECONDS = 3

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
				url = start_url + "/search#?q={}&latitude={}&longitude={}&radius=50"
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
			}f
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
				url = start_url + "/search#?q={}&latitude={}&longitude={}&radius=50&page=1".format(item[0], item[1], item[2])
				url_lists.append(url)

	luminati_zone_proxy_username = "lum-customer-hl_1dafde3b-zone-zone1"
	luminati_zone_proxy_pwd = "n9ndhce734x9"

	luminati_proxy_host = "zproxy.luminati.io"
	luminati_proxy_port = 22225

	for ind, url in enumerate(url_lists):
		if ind<200 or ind>300:
			continue
		logger.info("Index-------------------- -> {}".format(ind))

		proxy_ip = random_luminati_proxy()
		proxy_str = "{}:{}".format(luminati_proxy_host, luminati_proxy_port)
		auth_str = "{}-ip-{}".format(luminati_zone_proxy_username, proxy_ip, )
		
		# proxyauth_plugin_path = create_proxyauth_extension(
		# 		proxy_host=luminati_proxy_host,
		# 		proxy_port=luminati_proxy_port,
		# 		proxy_username=auth_str,
		# 		proxy_password=luminati_zone_proxy_pwd
		# 	)

		co = Options()
		co.add_argument("--start-maximized")
		#co.add_extension(proxyauth_plugin_path)
		driver = webdriver.Chrome(chrome_options=co)

		sleep(random.randrange(DRIVER_MEDIUM_WAITING_SECONDS))
		driver.get(url)
		logger.info(url)
		while(1):
			try:
				sleep(random.randrange(DRIVER_MEDIUM_WAITING_SECONDS))
				logger.info("Wait page loading")
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
				next_button = driver.find_element_by_xpath('//a[@class="next_page"]')
				driver.execute_script('window.scrollTo(0, ' + str(next_button.location['y']) + ');')
				next_button.click()
				sleep(random.randrange(DRIVER_MEDIUM_WAITING_SECONDS))
			except:
				break
		
		driver.quit()

def parse_span_by_xpath(xpath, html):
	lists = []
	path_div = html.q(xpath)
	if len(path_div) > 0:
		for row in path_div:
			t_str = row.x("text()").strip()
			if t_str != "":
				lists.append(t_str)

	return ",".join(lists)

def parse_services(xpath, html):
	services_div = html.q(xpath)
	service_list = []
	for row in services_div:
		title = row.x("h3/text()").strip()
		services = []

		for sub_row in row.q("ul/li"):
			services.append(str(sub_row.x("text()").strip()))

		t_str = title + ":" + str(services)
		service_list.append(t_str)
	
	return "\r\n".join(service_list)

def start_detail_scraping(threads_number):
	item_list = []
	with open(list_file) as csvfile:
		reader = csv.reader(csvfile)
		for i, list_item in enumerate(reader):
			if i > 0:
				item_list.append(list_item)

	threads = []
	while 1:
		while len(item_list) > 0:
			if len(threads) < threads_number:
				list_item = item_list.pop(0)

				thread_obj = threading.Thread(target=parse_detail_content,
											  args=(list_item,))
				threads.append(thread_obj)
				thread_obj.start()

			for thread in threads:
				if not thread.is_alive():
					thread.join()
					threads.remove(thread)
					print "Remain URL -> {0}".format(len(item_list))

		if len(item_list) == 0:
			break
				
def parse_detail_content(list_item):
	url = start_url + list_item[0]
	search_url = list_item[1]

	logger.info(url)
	html = s.load(url, use_cache = False)
	
	proxy = html.response.request.get("proxy")				
	logger.info(proxy.host + ":" + str(proxy.port))

	item = {}
	item["hotline"] = parse_span_by_xpath("//li[contains(@class,'hotline')]//span", html)
	item["tollfree"] = parse_span_by_xpath("//li[contains(@class,'tollfree')]//span", html)
	item["busphone"] = parse_span_by_xpath("//li[contains(@class,'bus-phone')]//span", html)
	item["language"] = parse_span_by_xpath("//li[contains(@class,'language')]//span", html)
	item["fax"] = parse_span_by_xpath("//li[contains(@class,'fax')]//span", html)
	item["tty"] = parse_span_by_xpath("//li[contains(@class,'TTY')]//span", html)

	hours = []
	hours_div = html.q("//li[contains(@class, 'hours-op')]//tr")
	if len(hours_div) > 0:
		for row in hours_div:
			tds = row.q("td")
			
			days = []
			for sub_row in tds:
				t_str = sub_row.x("text()").strip()
				days.append(t_str)

			if len(days) > 0:
				hours.append(",".join(days))

	item["hours"] = hours

	category_div = html.q("//div[@class='bread']/a[contains(@href,'search')]")
	category = []

	item_ind = -1
	for ind, row in enumerate(category_div):
		category.append(row.x("text()").strip())

	item["category"] = "/".join(category)

	header_div = html.q("//div[contains(@class,'location-head')]/h1")

	if len(header_div) > 0:
		item["title"] = header_div[0].x("text()").strip()
	else:
		item["title"] = ""

	item["website"] = parse_span_by_xpath("//li[@class='']/h3[contains(text(), 'Website')]/../span/a", html)
	item["beds"] = parse_span_by_xpath("//li[@class='']/h3[contains(text(), 'Beds')]/../span", html)
	item["wheelchair"] = parse_span_by_xpath("//li[@class='']/h3[contains(text(), 'Wheelchair')]/../span", html)
	item["established"] = parse_span_by_xpath("//li[@class='']/h3[contains(text(), 'Established')]/../span", html)
	item["maxmum_length"] = parse_span_by_xpath("//h3[contains(text(), 'Maximum Length of Stay')]/../span", html)
	item["pet_shelter"] = parse_span_by_xpath("//li[@class='']/h3[contains(text(), 'Pet Shelter')]/../span", html)
	item["description"] = parse_span_by_xpath("//div[contains(@class,'description')]/p", html)

	item["service_list"] = parse_services("//div[contains(@id, 'services')]//div[@class='js-accordion']", html)
	item["popup_service_list"] = parse_services("//div[contains(@class, 'pop-serve')]//div[@class='js-accordion']",html)

	item["counties_serve"] = html.q("//ul[@class='counties-served']/li/text()").join(" ")

	write_content(s, item, url, search_url)

def write_content(s, item, url, search_url):
	lock.acquire()

	content = [
		"Title", item["title"],
		"Category", item["category"],
		"Hotline", item["hotline"],
		"Toll Free", item["tollfree"],
		"Business", item["busphone"],
		"Language Spoken", item["language"],
		"TTY/TTD", item["tty"],
		"Fax", item["fax"],
		"Hours", "\r\n".join(item["hours"]),
		"Services", item["service_list"],
		"Populations Served", item["popup_service_list"],
		"Counties Served", item["counties_serve"],
		"Website", item["website"],
		"Wheelchair Accessible", item["wheelchair"],
		"Established", item["established"],
		"Maximum Length of Stay (days)", item["maxmum_length"],
		"Pet Shelter", item["pet_shelter"],
		"Description", item["description"],
		"Url", url,
		"Search Url", search_url,
	]
	s.save(content, detail_file)
	lock.release()

if __name__ == '__main__':
	
	#get_city_info()
	#get_geolocation()
	#get_start_urls()
	#start_selenium()
	start_detail_scraping(10)
