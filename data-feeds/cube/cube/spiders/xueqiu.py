# -*- coding: utf-8 -*-
import scrapy
import json
import redis
import os
import time
import datetime
import logging

from cube.items import CubeItem, OwnerItem, CubeProfitItem, CubeRebalanceItem, CubeRebalanceHistoryItem
from cube.crack.xueqiu_login import CrackXueQiu
from cube.spiders.hdf5 import Hdf5Utils
from cube.helper.string_helper import byte_to_str
from cube.helper.cube_helper import CubeHelper
from cube.helper.time_helper import long_to_date
from cube.config.config_helper import get_config

from cube.models.cube_item_wrapper import CubeItemWrapper
from cube.models.cube_profit_wrapper import cube_profit_wrapper_from_dict
from cube.models.cube_rebalancing_item_wrapper import cube_rebalance_item_wrapper_from_dict
from cube.models.cube_rebalancing_history_item_wrapper import cube_rebalance_history_item_wrapper_from_dict


class XueqiuSpider(scrapy.Spider):
    handle_httpstatus_list = [400]
    name = 'xueqiu'
    allowed_domains = ['xueqiu.com']
    start_urls = ['http://xueqiu.com/']
    login_result = True
    cookie_str = ''
    send_headers = {}
    cube_info_url = 'https://xueqiu.com/P/'
    # 调仓历史
    cube_rebalance_url = 'https://xueqiu.com/cubes/rebalancing/history.json?count=20&page=1&cube_symbol='
    # 收益历史
    # https://xueqiu.com/cubes/nav_daily/all.json?cube_symbol=ZH009248&&since=1546689578000&until=1578225578000
    # 这个接口的since和util必须要成对出现，否则无效
    cube_profit_url = 'https://xueqiu.com/cubes/nav_daily/all.json?cube_symbol='
    cube_detail_info = 'https://xueqiu.com/cubes/quote.json?code='
    cube_summary_url = 'https://xueqiu.com/cubes/rank/summary.json?ua=web&symbol='
    cube_rank_percent_url = 'https://xueqiu.com/cubes/data/rank_percent.json?cube_symbol=ZH166363&cube_id=166265&market=cn&dimension=annual&_=1579014357151'
    host = get_config('REDIS_HOST')
    passwd = get_config('REDIS_PASSWD')
    r = redis.Redis(host=host, password=passwd)
    # 是否用指定的代码爬取数据
    read_specify_symbol = False
    # 指定的组合代码
    symbols = ['ZH1244732', 'ZH009248', 'ZH1307218']
    logger = logging.getLogger(__name__)
    hdf5 = Hdf5Utils()
    # dictionary to map UserItem fields to Jmes query paths
    jmes_paths = {
        'name': 'name',
        'symbol': 'symbol',
        'market': 'market',
        'net_value': 'net_value',
        'closed_at': 'closed_at',  # 这个字段如果为空，则表示未关闭状态
    }

    owner_jmes_paths = {
        'id': 'id',
        'screen_name': 'screen_name'
    }

    def __init__(self):
        self.cube_helper = CubeHelper()
        self.cube_helper.generate_symbol_array()

    def start_requests(self):
        # 如果本地cookie json文件不存在, 那么先进行自动化登录
        if not os.path.exists('tmp_data/xueqiu_cookie.json'):
            crack = CrackXueQiu()
            login_result = crack.crack()
            if not login_result:
                print('自动登录不成功，停止')
                pass

        with open('tmp_data/xueqiu_cookie.json', 'r', encoding='utf-8') as f:
            list_cookies = json.loads(f.read())

        expired = False
        # 检测token是否过期，如果过期，那么进行重新登录。
        for item in list_cookies:
            if item.get('expiry') and ('token' in item['name']):
                if time.time() > item.get('expiry'):
                    expired = True
                    break

        if expired:
            crack = CrackXueQiu()
            login_result = crack.crack()
            if not login_result:
                print('自动登录不成功，停止')
                pass

            with open('tmp_data/xueqiu_cookie.json', 'r', encoding='utf-8') as f:
                list_cookies = json.loads(f.read())

        cookies = [item["name"] + "=" + item["value"] for item in list_cookies]
        self.cookie_str = '; '.join(item for item in cookies)
        print(f'从文件中读取的cookie: {self.cookie_str}')
        self.send_headers = {
            'cookie': self.cookie_str,
        }

        '''
        profit_list:
        所有的收益：https://xueqiu.com/cubes/nav_daily/all.json?cube_symbol=ZH1067693
        rebalance_list:
        调仓历史：https://xueqiu.com/cubes/rebalancing/history.json?cube_symbol=ZH009248&count=20&page=

        '''
        if self.read_specify_symbol:
            for s in self.symbols:
                profit_since_time = byte_to_str(self.r.get(f'{s}_profit_since_time'))
                self.logger.warning(f'redis---> get the profit_since_time: {profit_since_time}')
                params = ''
                if profit_since_time:
                    params = f'&since={profit_since_time}&until={int(time.time()) * 1000}'
                yield scrapy.Request(f'{self.cube_profit_url}{s}{params}', self.parse_cube_profit_list,
                                     headers=self.send_headers)
                yield scrapy.Request(f'{self.cube_rebalance_url}{s}', self.parse_cube_rebalance_list,
                                     headers=self.send_headers, cb_kwargs=dict(symbol=s))
        else:
            # cube_symbol_array = getattr(self.cube_helper, 'array0')
            # np_array = np.array(cube_symbol_array)
            # length = len(np_array)
            # index = 0
            # while index < length:
            #     random_step = random.randint(3, 6)
            #     last_index = index + random_step
            #
            #     if last_index > length:
            #         last_index = length
            #
            #     current_cube_symbol_array = np_array[index:last_index]
            #     index = last_index
            #     cube_symbol_str_array = ','.join(current_cube_symbol_array)
            #     yield scrapy.Request(f'{self.cube_detail_info}{cube_symbol_str_array}', self.parse_cube_info,
            #                          headers=self.send_headers,
            #                          cb_kwargs=dict(cube_symbol_array=current_cube_symbol_array))
            # 暂时这里用几个组合代码用来测试，测试完成之后，用上面的代码
            cube_symbol_array = ['ZH1244732', 'ZH009248', 'ZH1307218']
            yield scrapy.Request(f'{self.cube_detail_info}ZH1244732,ZH009248,ZH1307218', self.parse_cube_info,
                                 headers=self.send_headers,
                                 cb_kwargs=dict(cube_symbol_array=cube_symbol_array))

    def parse_cube_info(self, response, cube_symbol_array):
        """
        雪球组合发现页面请求之后对内容进行解析
        :param response: 请求返回来的json字符串
        :param cube_symbol_array: 请求组合信息的组合列表
        :return:
        """
        json_response = json.loads(response.body_as_unicode())
        for symbol in cube_symbol_array:
            if symbol in json_response:
                # 请求summary, 如果{symbol}_cube_info_{date}已经存在，那么说明数据已经抓取，
                # 则不进行重复抓取
                wrapper_item = CubeItemWrapper.from_dict(json_response[symbol])
                date = long_to_date(0)
                if not self.r.get(f'{symbol}_cube_info_{date}'):
                    yield scrapy.Request(f'{self.cube_summary_url}{symbol}', self.parse_cube_summary,
                                         headers=self.send_headers,
                                         cb_kwargs=dict(cube_wrapper_item=wrapper_item))

                # 请求收益列表
                # 通过上次一次存储的日期作为参数传进去，获取指定数据
                profit_since_time = byte_to_str(self.r.get(f'{symbol}_profit_since_time'))
                self.logger.warning(f'redis---> get the profit_since_time: {profit_since_time}')
                params = ''
                if profit_since_time:
                    params = f'&since={profit_since_time}&until={int(time.time()) * 1000}'
                yield scrapy.Request(f'{self.cube_profit_url}{symbol}{params}', self.parse_cube_profit_list,
                                     headers=self.send_headers)
                # 请求调仓记录
                # 当数据请求回来之后，根据本地存储的第一次数据的第一条id是否相等，如果相等，则不进行后续的爬取
                yield scrapy.Request(f'{self.cube_rebalance_url}{symbol}', self.parse_cube_rebalance_list,
                                     headers=self.send_headers, cb_kwargs=dict(symbol=symbol))

    def parse_cube_summary(self, response, cube_wrapper_item):
        """
        解析组合的summary内容,一天更新一次即可
        :param response:
        :param cube_wrapper_item:
        :return:
        """

        json_response = json.loads(response.body_as_unicode())
        total_score = json_response['total_score'] if 'total_score' in json_response else 0
        report_updated_time = json_response['report_updated_time'] if 'report_updated_time' in json_response else 0
        cube_wrapper_item.total_score = total_score
        cube_wrapper_item.report_updated_time = report_updated_time
        cube_item = CubeItem()
        cube_item['symbol'] = cube_wrapper_item.symbol
        cube_item['data_item'] = cube_wrapper_item
        date = long_to_date(report_updated_time)

        self.r.set(f'{cube_wrapper_item.symbol}_cube_info_{date}', 1)
        yield cube_item

    def parse_cube_profit_list(self, response):
        """
        解析组合数据数据，并存入h5文件
        :param response: 请求返回的json数组
        :return: None
        """
        if response.status == 200:
            json_response = json.loads(response.body_as_unicode())
            symbol = json_response[0]['symbol']
            cube_profit_item = CubeProfitItem()
            cube_profit_item['symbol'] = symbol
            cube_profit_item_wrapper = cube_profit_wrapper_from_dict(json_response[0]['list'])
            cube_profit_item['data_list'] = cube_profit_item_wrapper
            self.r.set(f'{symbol}_profit_since_time',
                       cube_profit_item_wrapper[len(cube_profit_item_wrapper) - 1].time)
            yield cube_profit_item

    def parse_cube_rebalance_list(self, response, symbol):
        """
        解析调仓记录
        :param response:
        :param symbol:
        :return:
        """
        data_list = []
        do_not_repeat = False
        if response.status == 200:
            json_response = json.loads(response.body_as_unicode())

            rebalance_items = CubeRebalanceItem()
            rebalance_items['symbol'] = symbol
            rebalance_item_wrapper = cube_rebalance_item_wrapper_from_dict(json_response['list'])
            rebalance_items['data_list'] = rebalance_item_wrapper

            local_latest_rebalacing = byte_to_str(self.r.get(f'{symbol}_saved_latest_rebalancing'))
            self.logger.warning(f'redis---> get the local_latest_rebalancing: {local_latest_rebalacing}')

            # yield rebalance_items
            for r in json_response['list']:
                if local_latest_rebalacing:
                    if int(local_latest_rebalacing) == int(r['id']):
                        do_not_repeat = True
                        break
                data_list += r['rebalancing_histories']

            page = json_response['page']

            if page == 1 and len(rebalance_item_wrapper) > 0:
                self.r.set(f'{symbol}_saved_latest_rebalancing',
                           rebalance_item_wrapper[0].rebalance_id)
            max_page = json_response['maxPage']
            print(f'{symbol}->进行第{page}页调仓数据爬取')
            if page < max_page and not do_not_repeat:
                page += 1
                self.cube_rebalance_url = f"https://xueqiu.com/cubes/rebalancing/history.json?count=20&page={page}&cube_symbol={symbol}"
                yield scrapy.Request(self.cube_rebalance_url, self.parse_cube_rebalance_list, headers=self.send_headers,
                                     cb_kwargs=dict(symbol=symbol), meta={"handle_httpstatus_all": True})
        else:
            self.logger.warning('request get 400.')
            pass

        if data_list and len(data_list) > 0:
            rebalance_history_items = CubeRebalanceHistoryItem()
            rebalance_history_items['symbol'] = symbol
            rebalance_history_wrapper_item = cube_rebalance_history_item_wrapper_from_dict(data_list)
            rebalance_history_items['data_list'] = rebalance_history_wrapper_item
            yield rebalance_history_items

    def parse_cube_list(self, response, uid=None, screen_name=None):
        """
        通过去查找创建的组合以及组合的基本信息
        :param response:
        :param uid:
        :param screen_name:
        :return:
        """
        json_response = json.loads(response.body_as_unicode())

        stock_json = json_response['data']['stocks']

        symbol_list_str = (",".join(str(s['symbol']) for s in stock_json))
        symbol_list = symbol_list_str.split(',')

        if uid is None:
            for s in symbol_list:
                yield scrapy.Request(f'{self.cube_info_url}{s}', self.parse_cube_detail_info, cb_kwargs=dict(symbol=s),
                                     headers=self.send_headers)
        else:
            cube_info_url = 'https://xueqiu.com/cubes/quote.json?code=' + symbol_list_str
            yield scrapy.Request(cube_info_url, self.parse_cube_info, headers=self.send_headers,
                                 cb_kwargs=dict(symbol_list=symbol_list))
