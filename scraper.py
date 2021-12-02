
from flask import Flask, jsonify, request
from flask_apscheduler import APScheduler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from os import error
from bs4 import BeautifulSoup
import urllib.request
import hashlib
import json
from pathlib import Path
import time

import os
import base64
import requests

import warnings
warnings.filterwarnings("ignore")


scheduler = APScheduler()

schedStat = 0
old_data = []
firstStart = True

app = Flask(__name__)

chrome_options = Options()
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument('--single-process')
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_prefs = {}
chrome_options.experimental_options["prefs"] = chrome_prefs

browser = webdriver.Remote(
    command_executor='http://hubcentral.duckdns.org:4444', options=chrome_options)

ALL_URLS = [['uk', 'https://www.hotukdeals.com/hot',
             'https://www.hotukdeals.com/new']]

BLACK_LIST = ['Tesco', 'Gamestop']

Img_direct = './img/'


def initData(filename):
    title_Hashs = []
    old_data = []

    if Path(filename).is_file() and Path('./title_hashs.json').is_file():
        with open('./title_hashs.json') as f:
            title_Hashs = json.load(f)
        with open(filename) as f:
            old_data = json.load(f)
    else:
        data = {}
        data["id"] = '0'
        data["categories"] = ["origine"]
        data["categories_trad"] = ['']
        data["coupon"] = ''
        data["title"] = "Origine"
        data['title_trad'] = ''
        data["img_src"] = "Logo Web Site"
        data["description_trad"] = "https://www.dealabs.com/"
        data["seller"] = "TheTeam"
        data["old_price"] = "Unknown"
        data["new_price"] = "Unknown"
        data["coupon"] = "0000000"
        data["hot"] = 'new'
        data["region"] = 'Morocco'
        data["description"] = "Where it all started Hotel Saint Ettienne ;)"
        data["url"] = "https://promochaser.com/"
        old_data.append(data)

    return(old_data, title_Hashs)


def writeJson(data, title_Hashs):
    with open("./Dataset.json", "w", encoding="UTF-8") as f:
        json.dump(data, f, indent=4, sort_keys=True, ensure_ascii=False)
    with open('./title_hashs.json', 'w', encoding="UTF-8") as f:
        json.dump(title_Hashs, f, indent=4, sort_keys=True, ensure_ascii=False)


def amazonAffUrl(url):
    if url.find('amazon') != -1:
        ind = url.find('?')
        if ind == -1:
            return url+"?linkCode=r02&tag=edwardmora10c-21&"
        return (url[:ind]+"?linkCode=r02&tag=edwardmora10c-21&")
    return url


def getArticles(url, region, title_Hashs):
    opner = urllib.request.build_opener()
    opner.addheaders = [
        ('User-agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)')]
    urllib.request.install_opener(opner)
    new_title_Hashs = []
    data = []
    try:
        fp = urllib.request.urlopen(url)
        # opener.open(url)

        mystr = fp.read()
        print('Link opened satrting process => ' + url, flush=True)
        fp.close()
    except Exception:
        print('Probleme opening the link no articles skipping => ' +
              region, flush=True)
        return(data, new_title_Hashs)
    soup = BeautifulSoup(mystr, 'html5lib', from_encoding="UTF-8")

    articles = soup.find_all('article', id=True)

    for article in articles:

        dat = {}
        dat['categories'] = []
        dat['region'] = region
        dat['new_price'] = ''
        dat['old_price'] = ''
        dat['coupon'] = ''
        dat['seller'] = ''
        dat['description'] = ''
        dat['img_src'] = ''
        dat['hot'] = 'new'
        dat['title_trad'] = ''
        dat['short_desc'] = ''

        if article.find('span', class_="cept-vote-temp vote-temp vote-temp--warm") != None:
            hot = article.find(
                'span', class_="cept-vote-temp vote-temp vote-temp--warm").text.strip()
            try:
                dat['hot'] = int(hot[0:len(hot)-1])
            except:
                dat['hot'] = hot

        title = article.find(
            'a', class_='cept-tt thread-link linkPlain thread-title--list')['title']
        ind = title.find('@')
        if ind != -1:
            title = title[:ind]
        dat['title'] = title.replace('"', '')
        hash_object = hashlib.md5(title.encode())
        dat['id'] = hash_object.hexdigest()
        skip = 0

        for it in title_Hashs:
            if dat['id'] == it:
                return(data, new_title_Hashs)

        if article.find('span', class_='thread-price text--b cept-tp size--all-l size--fromW3-xl') != None:
            dat['new_price'] = article.find(
                'span', class_='thread-price text--b cept-tp size--all-l size--fromW3-xl').text

        if article.find('span', class_='mute--text') != None:
            dat['old_price'] = article.find('span', class_='mute--text').text

        if article.find('input') != None:
            dat['coupon'] = article.find('input')['value']

        if article.find('span', class_='cept-merchant-name') != None:
            dat['seller'] = article.find(
                'span', class_='cept-merchant-name').text

        if article.find('strong', class_='thread-title').find('a') != None:
            dat['description'] = article.find(
                'strong', class_='thread-title').find('a')['href']

        if article.find('div', class_='cept-description-container') != None:
            # re.sub('\W+',' ',article.find('div',class_='cept-description-container').text.replace('"',' ').replace('Read more',''))
            dat['short_desc'] = ''

        for bl in BLACK_LIST:
            if title.find(bl) != -1:
                skip = 1

        if article.find('a', class_='cept-dealBtn', href=True) != None and skip != 1:
            try:
                response = urllib.request.urlopen(article.find(
                    'a', class_='cept-dealBtn', href=True)['href'], timeout=5)
                dat['url'] = response.geturl()

                response.close()
            except Exception:
                print('Error redirect skipping no seller url ', flush=True)
                dat['url'] = ''
            if article.find('img', class_='thread-image') != None:
                dat['img_src'] = Img_direct + str(dat['id']) + '.png'
                img_src = article.find('img', class_='thread-image')['src']

                if Path(dat['img_src']).is_file() != True:
                    try:
                        urllib.request.urlretrieve(img_src, dat['img_src'])
                    except Exception:
                        print('problem downloading Image skipping', flush=True)
                        dat['img_src'] = ''
            if dat['url'] != '':
                dat['url'] = amazonAffUrl(dat['url'])
                data.append(dat)
                new_title_Hashs.append(dat['id'])

    return(data, new_title_Hashs)


def getDesCat(data):
    for dat in data:
        count = 0
        try:
            fp = urllib.request.urlopen(dat['description'])
            mystr = fp.read()
            fp.close()
            dat['description'] = ''
            soup = BeautifulSoup(mystr, 'html5lib', from_encoding="UTF-8")
            cats = soup.find_all('li', class_='cept-breadcrumbsList-item')
            for cat in cats:
                if count != 0 and count < 3:

                    if dat["region"] == 'uk':
                        if cat.find('a').text.find('Groceries') != -1:
                            dat['categories'] .append('Daily Essentials')
                        dat['categories'].append(cat.find('a').text)

                count += 1
            #dat['description'] = re.sub('\W+',' ',soup.find('div',class_='cept-description-container').getText().replace('"',' '))

        except Exception:
            dat['description'] = ''
            print('Probleme opening the link no description skipping => ',
                  dat['id'], flush=True)
    return(data)


def getSite(url, region, title_Hashs):
    data, ha = getArticles(url, region, title_Hashs)
    print('done with articles : '+str(len(data)), flush=True)
    data = getDesCat(data)
    print('done with description', flush=True)
    return(data, ha)


def addProducts(data):

    user = 'ahmed'
    pythonapp = '723S A90a zNyB 12lB HsTd 56CW'
    url = 'https://promochaser.com/wp-json/wp/v2'
    cred = user + ':' + pythonapp
    token = base64.b64encode(cred.encode())
    header = {'Authorization': 'Basic ' + token.decode('utf-8')}

    for dat in data:
        media = {
            'file': open('./img/'+str(dat['id']) + '.png', 'rb'),
            'caption': dat['title']
        }

        image = requests.post(url + '/media', headers=header, files=media)

        imageId = str(json.loads(image.content)['id'])

        os.system('rm '+'./img/'+str(dat['id']) + '.png')

        desc = dat['description']
        if desc == '':
            desc = dat['short_desc']
        cats = []
        id_parent = 0
        for cat in dat['categories']:
            cat_json = {'name': cat, 'parent': id_parent}
            re = requests.post(url+'/categories',
                               headers=header, json=cat_json)
            res = json.loads(re.content)
            try:
                id_cat = res['id']

            except:
                try:
                    id_cat = res['data']['term_id']
                except:
                    id_cat = 0

            id_parent = id_cat
            cats.append(id_cat)
        seller = dat['seller']
        if dat['url'].find('amazon') != -1:
            seller = 'Amazon'
        seller_json = {'name': seller}
        re = requests.post(url+'/dealstore', headers=header, json=seller_json)
        res = json.loads(re.content)
        try:
            id_seller = res['id']
        except:
            try:
                id_seller = res['data']['term_id']
            except:
                id_seller = 0
        post = {
            'title': dat['title'],
            'status': 'publish',
            'content': desc,
            'author': '1',
            'format': 'standard',
            'featured_media': imageId,
            'categories': cats,
            'dealstore': [id_seller],
            'meta': {'rehub_offer_product_url': dat['url'],
                     'rehub_offer_product_price': dat['new_price'],
                     'rehub_offer_product_price_old': dat['old_price'],
                     'rehub_offer_product_coupon': dat['coupon'],
                     'rehub_offer_coupon_mask': '1',
                     'post_hot_count': str(dat['hot'])}
        }
        r = requests.post(url+'/posts', headers=header,  json=post)
        try:
            dat['id'] = json.loads(r.content)['id']
        except:
            dat['id'] = -1
    return data


def getAmazonArticle(html):
    bsoup = BeautifulSoup(html, 'html5lib')
    cat2 = ''
    if bsoup.find('div', id='wayfinding-breadcrumbs_feature_div') != None:
        cat2 = bsoup.find(
            'div', id='wayfinding-breadcrumbs_feature_div').find('li', id=False).text.strip()
    price = 0
    if bsoup.find('span', class_='a-price a-text-price a-size-medium apexPriceToPay') != None:
        price = bsoup.find(
            'span', class_='a-price a-text-price a-size-medium apexPriceToPay').find('span').text
    description = ""
    if bsoup.find('div', id="feature-bullets") != None:
        if bsoup.find('div', id="feature-bullets").find('ul') != None:
            descblocks = bsoup.find(
                'div', id="feature-bullets").find('ul').find_all('li', id=False)
            for desc in descblocks:
                description = description + desc.text
    return cat2, description, price


def getNewPrice(coup, old_price):
    ind = coup.find('£')
    price = float(old_price[1:])
    if ind != -1:
        return(price - float(coup[1:]))
    return(price - price*(float(coup[:len(coup)-1])/100))


def getBrowserConnect(amazonUrl):

    global browser
    browser.set_window_size(1920, 1080)

    browser.get(amazonUrl)

    browser.find_element_by_xpath("//*[contains(text(), 'Sign in')]").click()
    time.sleep(2)
    browser.find_element_by_id('ap_email').send_keys('pypscrapmaz@gmail.com')
    time.sleep(2)
    browser.find_element_by_id('continue').click()
    time.sleep(1)
    browser.find_element_by_id('ap_password').send_keys('cm23101958')
    time.sleep(2)
    browser.find_element_by_id('signInSubmit').click()
    time.sleep(2)
    print(browser.current_url, flush=True)


def scrapAmazon(amazonUrl, title_Hashs):

    global browser

    browser.get(amazonUrl)

    click = browser.find_element_by_xpath("//*[contains(text(), 'Vouchers')]")
    browser.execute_script("arguments[0].click();", click)
    time.sleep(2)
    browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(2)
    soup = BeautifulSoup(browser.page_source, 'html5lib')

    divs = soup.find_all(
        'div', class_='a-section coupon-shoveler coupon-shoveler-common')
    data = []
    new_title_Hashs = []
    for div in divs:
        cat = div.find(
            'h3', class_='a-color-information coupon-carousel-heading a-text-bold').text
        tet = ''
        if cat.find('Toys') != -1:
            tet = 'Family & Kids'
        elif cat.find('Home, Kitchen, Furniture & Tools') != -1:
            tet = 'Home & Living'
        elif cat.find('Elektronic, Computers & Wireless') != -1:
            tet = 'Electronics'
        else:
            tet = cat
        print('getting : ' + tet, flush=True)
        sections = div.find_all('li', class_='a-carousel-card')
        indice = True
        count = 0
        for sec in sections:
            if indice and count < 5:
                dat = {}
                dat['categories'] = [tet]
                dat['region'] = 'uk'
                dat['old_price'] = ''
                dat['coupon'] = 'Applied at checkout on Amazon'
                dat['seller'] = 'Amazon'
                dat['img_src'] = ''
                dat['hot'] = 'new'
                dat['title_trad'] = ''
                dat['short_desc'] = ''
                coupon = sec.find(
                    'span', class_='a-size-medium a-color-success a-text-bold').text.strip()[5:]
                img = sec.find('a', title="Collect Voucher").find('img')['src']
                dat['id'] = sec.find('div', class_='a-box coupon')['id'][11:]
                for it in title_Hashs:
                    if dat['id'] == it:
                        indice = False
                if indice:
                    link = sec.find(
                        'a', class_='a-size-base a-link-normal coupon-title-text', href=True)
                    url = link['href']
                    dat['title'] = link['title']
                    uri = "https://www.amazon.co.uk"+url
                    browser.get(uri)
                    ignore = False
                    browser.execute_script(
                        "window.scrollTo(0,document.body.scrollHeight)")
                    uri = browser.current_url
                    time.sleep(2)
                    if uri.find('coupon') != -1:
                        sp = BeautifulSoup(browser.page_source, 'html5lib')
                        if sp.find('span', class_='a-size-base clptitle a-text-bold') != None:
                            uri = sp.find('span', class_='a-size-base clptitle a-text-bold').find(
                                'a', class_='a-link-normal', href=True)['href']
                            ind = uri.find('&s')
                            if ind != -1:
                                uri = uri[:ind]
                            browser.get(uri)

                        else:
                            ignore = True
                        # browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                        # time.sleep(2)
                    if ignore == False:
                        cat2, dat['description'], dat['old_price'] = getAmazonArticle(
                            browser.page_source)
                        if dat['old_price'] != 0:

                            dat['url'] = uri
                            if cat2 != '':
                                dat['categories'].append(cat2)
                            dat['img_src'] = "./img/" + str(dat['id']) + '.png'
                            if Path(dat['img_src']).is_file() != True:
                                try:
                                    urllib.request.urlretrieve(
                                        img, dat['img_src'])
                                except Exception:
                                    print(
                                        'problem downloading Image skipping', flush=True)
                                    dat['img_src'] = ''
                            dat['new_price'] = '£' + \
                                str(getNewPrice(coupon, dat['old_price']))[:4]
                            if dat['img_src'] != '':
                                count += 1
                                dat['url'] = amazonAffUrl(dat['url'])
                                data.append(dat)
                                new_title_Hashs.append(dat['id'])

        indice = True
    return(data, new_title_Hashs)


def main():
    global firstStart
    global old_data
    global browser
    if firstStart:
        getBrowserConnect('https://www.amazon.co.uk/')
        firstStart = False
    old_data, title_Hashs = initData("./Dataset.json")
    for url in ALL_URLS:
        data, ha = getSite(url[1], url[0], title_Hashs)
        copie_data = data
        title_Hashs = title_Hashs + ha
        data, ha = scrapAmazon(
            'https://www.amazon.co.uk/', title_Hashs)
        copie_data = copie_data + data
        print('Adding products', flush=True)
        copie_data = addProducts(copie_data)
        print('Done Adding products : '+str(len(copie_data)), flush=True)
        old_data = old_data + copie_data
        title_Hashs = title_Hashs + ha
        print('done with ', flush=True)
    writeJson(old_data, title_Hashs)


@app.route("/")
def index():
    return jsonify({"message": "Go to /start to lunch the script or /stop to stop the one runnig"})


@app.route("/start")
def start():
    freq = request.args.get('freq')
    try:
        if freq != None and int(freq) > 0:
            global schedStat
            global scheduler
            if schedStat == 0:
                scheduler.start()
                scheduler.add_job(id='Scheduled Task', func=main, trigger='interval',
                                  minutes=int(freq), max_instances=1)
            elif schedStat == -1:
                scheduler = APScheduler()
                scheduler.start()
                scheduler.add_job(id='Scheduled Task', func=main, trigger='interval',
                                  minutes=int(freq), max_instances=1)
            else:
                return jsonify({"message": "Job already running", "val": 1})
            schedStat = 1
            idJob = scheduler.get_jobs()

            return(jsonify({"message": "Job Started", "job": idJob[0].name, "freq": freq, "val": 10}))
        else:
            return(jsonify({"message": "no freq ", "val": 2}))
    except error as e:
        print(e)
        return (jsonify({"message": "Problem starting the Job ", "val": 3}))


@app.route("/stop")
def stop():
    global schedStat
    global scheduler
    if schedStat == 1:
        idJob = scheduler.get_jobs()
        print(idJob)
        scheduler.shutdown(wait=False)
        schedStat = -1
        return jsonify({"message": "stoped", "job": idJob[0].name})
    else:
        return jsonify({"message": "No Job running"})


@app.route("/status")
def status():

    global schedStat
    if schedStat == 0:
        return jsonify({"message": "No Job started"})
    elif schedStat == 1:
        return jsonify({"message": "Job running"})
    else:
        return jsonify({"message": "Job stoped"})


@app.route("/data")
def data():
    return jsonify(old_data)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=4000)
