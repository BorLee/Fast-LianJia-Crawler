import logging
from pathlib import Path

from pyquery import PyQuery as pq

from config import config
from lian_jia import Community
from util.orm import Session

from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent.joinpath('../data/').resolve()

def removehtml(context):
    import re
    context = re.sub(r'</?\w+[^>]*>','',context)
    context = context.replace(' ','')
    context = context.replace('\n','')
    return context

def parse_community_detail(community_id,city_id):
    save_file = DATA_DIR.joinpath(f'{community_id}.html')

    if save_file.exists():
        if city_id == 310000 or city_id == 320500:
            context = BeautifulSoup(save_file.read_text(encoding='utf-8'),'lxml')
            context = BeautifulSoup(context.prettify(),'lxml')
            context = context.find_all(attrs={'class':'res-info fr'})[0]
            context = BeautifulSoup(str(context),'lxml')

            fkeys = str(context.find(attrs={'class':'t'}))
            fvalues = str(context.find(attrs={'class':'p'})) + str(context.find(attrs={'class':'u'}))

            keys = [removehtml(str(e)).rstrip('：') for e in context.find_all('label')]
            values = [removehtml(str(e)) for e in context.find_all(attrs={'class':'other'})]

            keys = [removehtml(fkeys)] + keys
            values = [removehtml(fvalues)] + values
            detail = dict(zip(keys, values))
        else:
            d = pq(save_file.read_text(encoding='utf-8'))
            keys = [e.text.rstrip('：') for e in d('span.hdic_key')]
            values = [e.text for e in d('span.hdic_value')]
            detail = dict(zip(keys, values))

        if not detail:
            logging.warning(f'# 页面已找到, 但其中未发现小区详情信息, community_id={community_id}')

        return detail

    else:
        logging.error(f'# 详情页面不存在, community_id={community_id}')


def parse_all_communities(city_id):
    db_session = Session()

    communities = db_session.query(Community).filter(
        Community.city_id == city_id,
        Community.detail == None,
        Community.page_fetched_at != None
    ).all()

    total_count = len(communities)
    logging.info(f'city_id={city_id}, 待分析={total_count}')

    for i, a_community in enumerate(communities):
        detail = parse_community_detail(a_community.id,city_id)

        if detail:
            a_community.detail = detail

        if (i + 1) % 100 == 0 or (i == total_count - 1):
            logging.info(f'进度={i + 1}/{total_count}, 剩余={total_count - i - 1}')
            db_session.commit()

    logging.info('已全部分析完成.')
    db_session.close()


def main():
    parse_all_communities(config.city_id)


if __name__ == '__main__':
    main()
