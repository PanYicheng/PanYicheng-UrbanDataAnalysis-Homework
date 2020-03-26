#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!/usr/bin/env python
# coding: utf-8

import requests
from bs4 import BeautifulSoup
import urllib
import re
import json
import time
import pickle
import os
# from tqdm import tqdm

sleep_time = 1 # seconds


# In[69]:


def get_search_url(keyword_chn, page=1):
    return 'https://search.bilibili.com/all?keyword={keyword}&page={page}'        .format(keyword=urllib.parse.quote(keyword_chn.encode('utf-8')), page=page)


def get_video_url_list(search_page_url):
    req = requests.get(search_page_url)
    soup = BeautifulSoup(req.text, 'html.parser')
    try:
        video_page_urls = ['https://'+_.select('a[class="img-anchor"]')[0].attrs['href'].lstrip('/') for _ in soup.select('ul[class="video-list clearfix"]')[0].children]
        last_page_btns = soup.select('li[class="page-item last"] > button[class="pagination-btn"]')
        if len(last_page_btns) > 0:
            total_pages = int(last_page_btns[0].text.strip())
        else:
            total_pages = max([int(_.text) for _ in soup.select('li[class="page-item"] > button')])
    except:
        video_page_urls = []
        total_pages = 0
    return video_page_urls, total_pages
    
    
def get_all_video_url_list(keyword, max_page=5):
    first_page_url = get_search_url(keyword)
    print('Retrieving {}'.format(first_page_url), end='')
    video_urls, total_pages = get_video_url_list(first_page_url)
    print(' Num:', len(video_urls))
    print('Total number of pages:', total_pages)
    time.sleep(sleep_time)
    for i in range(2, min(total_pages+1, max_page+1)):
        search_page_url=get_search_url(keyword, page=i)
        print('Retrieving {}'.format(search_page_url), end='')
        next_video_urls, _ = get_video_url_list(search_page_url)
        print(' Num:', len(next_video_urls))
        video_urls.extend(next_video_urls)
        time.sleep(sleep_time)
    return video_urls


def get_video_info_from_page(video_page):
    headers = {

        'host': 'www.bilibili.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
    }
    video_page_req = requests.get(video_page, headers=headers)
    video_soup = BeautifulSoup(video_page_req.text, 'html.parser')
    title = video_soup.select('title')[0].text
    video_info = json.loads(
        video_soup.select('script[type="application/ld+json"]')[0].text)
    for script in video_soup.select('script'):
        if re.search('"cid":', script.text):
            break
    try:
        cid_str = script.text[script.text.find('"cid":')+6:]
        cid_str = cid_str[: cid_str.find(',')]
        cid = int(cid_str)
        return cid, title, video_info
    except:
        print("Cannot get comment id from video page {}".format(video_page))
        return None, None, None


def get_comment(cid):
    url = 'http://comment.bilibili.com/{}.xml'.format(cid)
    req = requests.get(url)
    html = req.content
    html_doc=str(html,'utf-8')   #修改成utf-8

    #解析
    soup = BeautifulSoup(html_doc,"lxml")

    results = soup.find_all('d')

    contents = [x.text for x in results]
    
    #保存结果
    # table_dict = {"contents":contents}
    # df = pd.DataFrame(table_dict)
    # df.to_csv("bibi.csv",encoding='utf-8')
    return contents


# In[34]:


province_names = [
                # 直辖市
                '直辖市', 
                # 自治区类别
                  '新疆自治区', '西藏自治区', '宁夏自治区', '内蒙古自治区', 
                  '广西自治区',
                # 常规省份
                  '黑龙江', '吉林', '辽宁', '河北', '山东', '江苏', '安徽',
                  '浙江', '福建', '广东', '海南', '云南', '贵州', '四川',
                  '湖南', '湖北', '河南', '山西', '陕西', '甘肃', '青海',
                  '江西', '台湾', 
                # 特别行政区
                  '特别行政区']
city_names=[
    # 直辖市
    ['北京','天津','上海','重庆'],
    # 自治区类别
    ['乌鲁木齐', '克拉玛依'],
    ['拉萨'],
    ['银川', '石嘴山', '吴忠', '固原', '中卫'],
    ['呼和浩特', '包头', '乌海', '赤峰', '通辽', '鄂尔多斯', '呼伦贝尔', 
        '巴彦淖尔', '乌兰察布'],
    ['南宁', '柳州', '桂林', '梧州', '北海', '崇左', '来宾', '贺州', '玉林', 
        '百色', '河池', '钦州', '防城港', '贵港'],
    # 常规省份
    ['哈尔滨', '大庆', '齐齐哈尔', '佳木斯', '鸡西', '鹤岗', '双鸭山', '牡丹江', 
        '伊春', '七台河', '黑河', '绥化'],
    ['长春', '吉林', '四平', '辽源', '通化', '白山', '松原', '白城'],
    ['沈阳', '大连', '鞍山', '抚顺', '本溪', '丹东', '锦州', '营口', '阜新', 
        '辽阳', '盘锦', '铁岭', '朝阳', '葫芦岛'],
    ['石家庄', '唐山', '邯郸', '秦皇岛', '保定', '张家口', '承德', '廊坊', '沧州',
         '衡水', '邢台'],
    ['济南', '青岛', '淄博', '枣庄', '东营', '烟台', '潍坊', '济宁', '泰安', 
        '威海', '日照', '莱芜', '临沂', '德州', '聊城', '菏泽', '滨州'],
    ['南京', '镇江', '常州', '无锡', '苏州', '徐州', '连云港', '淮安', '盐城', 
        '扬州', '泰州', '南通', '宿迁'],
    ['合肥', '芜湖', '蚌埠', '淮南', '马鞍山', '淮北', '铜陵', '安庆', '黄山', 
        '阜阳', '宿州', '滁州', '六安', '宣城', '池州', '亳州', '潜山'],
    ['杭州', '嘉兴', '湖州', '宁波', '金华', '温州', '丽水', '绍兴', '衢州', 
        '舟山', '台州'],
    ['福州', '厦门', '泉州', '三明', '南平', '漳州', '莆田', '宁德', '龙岩'],
    ['广州', '深圳', '汕头', '惠州', '珠海', '揭阳', '佛山', '河源', '阳江', 
        '茂名', '湛江', '梅州', '肇庆', '韶关', '潮州', '东莞', '中山', '清远', 
        '江门', '汕尾', '云浮'],
    ['海口', '三亚'],
    ['昆明', '曲靖', '玉溪', '保山', '昭通', '丽江', '普洱', '临沧'],
    ['贵阳', '六盘水', '遵义', '安顺'],
    ['成都', '绵阳', '德阳', '广元', '自贡', '攀枝花', '乐山', '南充', '内江', 
        '遂宁', '广安', '泸州', '达州', '眉山', '宜宾', '雅安', '资阳'],
    ['长沙', '株洲', '湘潭', '衡阳', '岳阳', '郴州', '永州', '邵阳', '怀化', 
        '常德', '益阳', '张家界', '娄底'],
    ['武汉', '襄樊', '宜昌', '黄石', '鄂州', '随州', '荆州', '荆门', '十堰', 
        '孝感', '黄冈', '咸宁'],
    ['郑州', '洛阳', '开封', '漯河', '安阳', '新乡', '周口', '三门峡', '焦作', 
        '平顶山', '信阳', '南阳', '鹤壁', '濮阳', '许昌', '商丘', '驻马店'],
    ['太原', '大同', '忻州', '阳泉', '长治', '晋城', '朔州', '晋中', '运城', 
        '临汾', '吕梁'],
    ['西安', '咸阳', '铜川', '延安', '宝鸡', '渭南', '汉中', '安康', '商洛', 
        '榆林'],
    ['兰州', '天水', '平凉', '酒泉', '嘉峪关', '金昌', '白银', '武威', '张掖', 
        '庆阳', '定西', '陇南'],
    ['西宁'],
    ['南昌', '九江', '赣州', '吉安', '鹰潭', '上饶', '萍乡', '景德镇', '新余', 
        '宜春', '抚州'],
    ['台北', '台中', '基隆', '高雄', '台南', '新竹', '嘉义'],
    # 特别行政区
    ['香港', '澳门']
]


# In[ ]:


city_index =  1


# In[70]:


for city_index in range(16, len(city_names)):
    if city_index == 7:
        continue
    keyword=city_names[city_index]
    save_name='anhui_'+str(city_index)
    print('City Name:', keyword)
    all_video_urls = get_all_video_url_list(keyword, max_page=20)
    print('Crawl videos:', len(all_video_urls))
    
    if os.path.exists(os.path.join('bilibili-comment-by-city', save_name+'.pkl')):
        with open(os.path.join('bilibili-comment-by-city', save_name+'.pkl'), 'rb') as f:
            comment_dict = pickle.load(f)
    else:
        comment_dict = dict()
        
    # pbar = tqdm(total=len(all_video_urls), ascii=True)
    debug = True
    for i, video_url in enumerate(all_video_urls):
        print('[{:3d}/{:3d}]'.format(i, len(all_video_urls)), end=' ')
        if video_url in comment_dict:
            if debug:
                print('Already exists, Skipping!')
        else:
            succeed = True
            if debug:
                print('Getting comment of {}'.format(video_url), end='')
            try:
                cid, title, video_info = get_video_info_from_page(video_url)
                time.sleep(sleep_time)
                comment = get_comment(cid)
                comment_dict[video_url] = (cid, title, video_info, comment)
                time.sleep(sleep_time)
            except:
                succeed = False
            if debug:
                print(' Succeed!' if succeed else ' Failed!')
    #     pbar.update(1)


    os.makedirs('bilibili-comment-by-city', exist_ok=True)
    with open(os.path.join('bilibili-comment-by-city', save_name+'.pkl'), 'wb') as f:
        pickle.dump(comment_dict, f)

