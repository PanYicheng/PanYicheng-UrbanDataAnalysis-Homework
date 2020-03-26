import time
import json
import requests
from functools import wraps
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from tqdm import tqdm


class HttpCodeException(Exception):
    pass


def retry(retry_count=5, sleep_time=1):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            for i in range(retry_count):
                try:
                    res = func(*args, **kwargs)
                    return res
                except:
                    time.sleep(sleep_time)
                    continue
            return None
        return inner
    return wrapper


def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").text


@retry()
def get_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.87 Mobile Safari/537.36',
        'Host': 'movie.douban.com',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Referer': 'https://movie.douban.com/top250?start=25&filter='
    }

    # 使用代理,尽量减少IP被封的可能
    # res = requests.get(url, headers=headers, proxies={"http": "http://{}".format(get_proxy())})
    # 不适用代理的方法
    res = requests.get(url, headers=headers)
    time.sleep(3)   # 这里一定要sleep3秒,不然,频繁的抓取会导致IP被封
#     print(res.status_code)
    if res.status_code != 200:
        raise HttpCodeException

    return res.text


def extract_info(html):
    """
    获取电影的详细信息
    :param html:
    :return:
    """

    soup = BeautifulSoup(html, 'html.parser')

    area = ""
    info_div = soup.find('div', attrs={'id': 'info'})
    for child in info_div.children:
        if child.string and child.string.startswith('制片国家/地区'):
            area = child.next_sibling.string.strip()

    info_script = soup.find('script', attrs={'type': 'application/ld+json'})
    info_text = info_script.text.replace('\r', '').replace('\n', '')
    json_data = json.loads(info_text)

    info = {}
    info['name'] = json_data['name']
    info['director'] = json_data['director']    # 导演
    info['actor'] = json_data['actor']   # 主演
    info['datePublished'] = json_data['datePublished']  # 发型日期
    info['genre'] = json_data['genre']   # 电影类型
    info['ratingCount'] = json_data['aggregateRating']['ratingCount'] # 评价人数
    info['ratingValue'] = json_data['aggregateRating']['ratingValue'] # 评分
    info['area'] = area   # 制作国家地区
    desc = list(soup.find('div', attrs={'class': 'indent', 'id': 'link-report'}).children)[3].text.replace('\n', '').replace('\u3000', '').strip()
    info['description'] = desc
    return info


def get_info_by_url(url):
    try:
        html = get_html(url)
        info = extract_info(html)
    except:
        return url
    return info


def produce_url():
    """
    每个页面有25个电影，共10个页面，这10个页面的url可以自己生成
    :return:
    """
    url_style = "https://movie.douban.com/top250?start={index}&filter="
    url_lst = []
    for i in range(0, 250, 25):
        url = url_style.format(index=i)
        print(url)
        url_lst.append(url)

    return url_lst


def get_info_url(page_url):
    """
    获取每个页面25个电影的详细信息的url
    :param page_url:
    :return:
    """
    html = get_html(page_url)
    soup = BeautifulSoup(html, 'html.parser')

    url_lst = []
    ol_node = soup.find('ol', class_='grid_view')
    pic_nodes = ol_node.find_all('div', class_='pic')
    for pic_node in pic_nodes:
        a = pic_node.find('a')
        href = a['href']
        url_lst.append(href)

    return url_lst


def run_multi_thread():
    """
    多线程爬取
    :return:
    """
    res_file = open('movie_data', 'w')
    t1 = time.time()
    url_lst = []
    page_url_lst = produce_url()

    for page_url in page_url_lst:
        page_url_lst = get_info_url(page_url)
        url_lst.extend(page_url_lst)

    # 10个线程进行爬取
    tpool = ThreadPoolExecutor(max_workers=10)
    pbar = tqdm(total=len(url_lst), ascii=True)
    def thread_func(url):
        info = get_info_by_url(url)
        pbar.update(1)
        return info
    obj = []
    for url in url_lst:
        t = tpool.submit(thread_func, url)
        obj.append(t)
    tpool.shutdown()
    for t in obj:
        data = t.result()
        if isinstance(data, str):
            print(data)
        else:
            res_file.write(json.dumps(data, ensure_ascii=False) + "\n")

    res_file.close()
    t2 = time.time()
    print("耗时" + str(t2-t1))


if __name__ == '__main__':
    run_multi_thread()