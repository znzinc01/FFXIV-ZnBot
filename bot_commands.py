import random
import json
import requests
import traceback

# Import Keys
with open('./keys.json', 'r') as keyFile:
    key = json.loads(keyFile.read())
    

def dice(args):
    limit, rolls = 999, 1
    try:
        if len(args) > 0:
            limit = int(args[0])
        if len(args) > 1:
            rolls = int(args[1])
        if not (2<= limit <= 10000 and 1 <= rolls <= 100):
            raise ValueError
        message = '**최대값 {} 주사위 {}회:** '.format(limit, rolls) + \
            ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    except:
        message = '**잘못된 입력입니다:** 크기는 10000 이하, 개수는 100 이하의 자연수로 입력해 주세요.'
    
    return message, None


def selector(args):
    if 2 <= len(args) <= 100:
        message = '**선택 결과:** ' + args[random.randint(0, len(args) - 1)]
    else:
        if len(args) < 2:
            message = '**잘못된 입력입니다:** 항목을 2개 이상 입력해 주세요.'
        else:
            message = '**잘못된 입력입니다:** 항목을 100개 이하로 입력해 주세요.'
    
    return message, None


def item_sellers(args):
    input_item_name = str(' '.join(args))
    r_name2id = requests.post(key['API_item_name_to_id'], {'name': input_item_name})
    item_list = json.loads(r_name2id.text)
    
    # No item found with given name
    if not item_list:
        message = '**{}** 의 검색 결과가 없습니다.'.format(input_item_name)
        return message, None

    item_name = item_list[0]['label']
    r_detail = requests.post(key['API_item_detail'], {'id': item_list[0]['id']})
    item_detail = json.loads(r_detail.text)
    item_page_url = 'https://ff14.tar.to/item/view/{}'.format(item_detail['item']['id'])
    iconid = int(item_detail['item']['icon'])
    icon_image_url = key['API_item_url_base'] + '{:06d}/{:06d}.tex.png'.format(int(iconid / 1000) * 1000, iconid)
    
    enpc_raw_list = item_detail['enpc']
    senpc_raw_list = item_detail['senpc']

    enpc_list, senpc_list = [], []
    items = item_detail['items']
    
    housing_x = [-1, 0]
    
    for enpc in enpc_raw_list:
        if enpc['x'] is None:
            continue
        name = enpc['name']
        location = '하우징 혹은 특수필드' if enpc['x'] in housing_x else '{}({}, {})'.format(enpc['placename'],
                                                                                       round(enpc['x'], 1),
                                                                                       round(enpc['y'], 1))
        price =  item_detail['item']['price_a']
        if not [name, location, price] in enpc_list:
            enpc_list.append([name, location, price])
    
    for senpc in senpc_raw_list:
        if not senpc['x']:
            continue
        name = senpc['enpc_name']
        location = '하우징 혹은 특수필드' if senpc['x'] in housing_x else '{}({}, {})'.format(senpc['name'],
                                                                                         round(senpc['x'], 1),
                                                                                         round(senpc['y'], 1))
        exchange = []
        for i in range(1,4):
            if senpc['target_id{}'.format(i)] is None or senpc['target_id{}'.format(i)] == 0:
                break
            target = items[str(senpc['target_id{}'.format(i)])]
            if senpc['target_hq{}'.format(i)]:
                target += ' HQ'
            if senpc['target_collectivity{}'.format(i)] is None:
                senpc['target_collectivity{}'.format(i)] = 0
            if senpc['target_collectivity{}'.format(i)] > 0:
                target += ' 소장 가치 {} 이상'.format(senpc['target_collectivity{}'.format(i)])
            target += ' {}개'.format(senpc['target_quantity{}'.format(i)])
            exchange.append(target)
        if not [name, location, exchange] in senpc_list:
            senpc_list.append([name, location, ', '.join(exchange)])
    
    message = '**{}** 을(를) 구할 수 있는 NPC 정보입니다. '.format(item_name) + \
        item_page_url

    
    if not enpc_list and not senpc_list:
        message = '**{}** 을(를) 구할 수 있는 NPC 정보가 없습니다.'.format(item_name)
        return message, None
    
    elif not senpc_list:
        enpc_string = '\n'.join(['{} {}'.format(x[1], x[0]) for x in enpc_list[0:3]])
        if len(enpc_list) > 3:
            enpc_string += ' 등'
        enpc_dict = {'name': '{}길로 구입하기'.format(enpc_list[0][2]),
                    'value': enpc_string}
        return message, [item_name + ' 입수 정보',
                         '위 링크에서 더 많은 정보를 확인할 수 있습니다.',
                         item_page_url,
                         icon_image_url,
                         enpc_dict]
        
    elif not enpc_list:
        senpc_string = '\n'.join(['{} {}: {}'.format(x[1], x[0], x[2]) for x in senpc_list[0:3]])
        if len(senpc_list) > 3:
            senpc_string += ' 등'
        senpc_dict = {'name': '아이템으로 교환하기',
                    'value': senpc_string}
        return message, [item_name + ' 입수 정보',
                         '위 링크에서 더 많은 정보를 확인할 수 있습니다.',
                         item_page_url,
                         icon_image_url,
                         senpc_dict]
        
    else:
        enpc_string = '\n'.join(['{} {}'.format(x[1], x[0]) for x in enpc_list[0:2]])
        if len(enpc_list) > 2:
            enpc_string += ' 등'
        senpc_string = '\n'.join(['{} {}: {}'.format(x[1], x[0], x[2]) for x in senpc_list[0:2]])
        if len(senpc_list) > 2:
            senpc_string += ' 등'
        
        enpc_dict = {'name': '{}길로 구입하기'.format(enpc_list[0][2]),
                    'value': enpc_string}
        senpc_dict = {'name': '아이템으로 교환하기',
                    'value': senpc_string}
        return message, [item_name + ' 입수 정보',
                         '위 링크에서 더 많은 정보를 확인할 수 있습니다.',
                         item_page_url,
                         icon_image_url,
                         enpc_dict,
                         senpc_dict]
        

def get_command_name(name):
    command_dict = {'주사위': ['주사위'],
                    '선택': ['선택'],
                    '판매정보': ['판매정보', '판매검색', '판매', '교환정보', '교환검색', '교환'],
                    '도움말': ['도움말', '도움']
    }
    for cmd in command_dict.keys():
        for alias in command_dict[cmd]:
            if name == alias or name == '!' + alias:
                return cmd
    return None


def help(args):
    message = '`FFXIV-ZnBot 도움말 (2.0 / 20200802)`'
    cmd = get_command_name(args[0]) if len(args) > 0 else None
    if cmd is None or cmd == '도움말':
        return message, ['전체 도움말','','','',
                         {'name': '!주사위', 'value':'무작위 주사위를 굴립니다. 최대 값이나 회수를 변경할 수도 있습니다.'},
                         {'name': '!선택', 'value':'제시한 선택지 중에서 고릅니다.'},
                         {'name': '!판매정보', 'value':'아이템을 구입할 수 있는 NPC 정보를 보여줍니다.'},
                         {'name': '!도움말', 'value':'본 도움말을 표시합니다. 뒤에 명령어를 입력하면 명령어에 대한 자세한 도움말을 볼 수 있습니다.'},
                         {'name': '개인정보처리방침 / 문의, 버그제보', 'value': key['bot_webpage']},
                         {'name': 'Credits', 'value': '기재되어있는 회사 명 · 제품명 · 시스템 이름은 해당 소유자의 상표 또는 등록 상표입니다.\n' +\
                                                      '(C) 2010 - 2020 SQUARE ENIX CO., LTD. All Rights Reserved. Published in Korea by ACTOZSOFT CO., LTD.\n' +\
                                                      '아이템 판매 NPC 정보는 타르토맛 타르트 [ff14.tar.to](https://ff14.tar.to) 에서 제공받습니다.'}]
    else:
        if cmd == '주사위':
            return message, ['!주사위 (최대값) (회수)','최대 값이나 회수를 지정하여 주사위를 굴립나다. (기본값: !주사위 999 1)','','',
                             {'name': '최대값', 'value': '2부터 10000까지의 값을 입력할 수 있습니다.\n 숫자를 하나만 입력하면 무조건 최대값으로 처리됩니다.'},
                             {'name': '회수', 'value': '1부터 100까지의 값을 입력할 수 있습니다. \n 숫자를 하나만 입력하면 1회만 굴립니다.'},
                             {'name': '예시: !주사위 99 5', 'value': '최대값이 99인 주사위를 5번 굴립니다.'}]
        if cmd == '선택':
            return message, ['!선택 (선택지1) (선택지2) ...', '봇에게 전달한 선택지 중 하나를 고릅니다.', '','',
                             {'name': '선택지', 'value': '선택지는 띄어쓰기로 구분합니다. 2개 이상 100개 이하까지 처리할 수 있습니다.'},
                             {'name': '예시: !선택 울다하 그리다니아 림사 로민사', 'value': '울다하, 그리다니아, 림사, 로민사 중 하나를 고릅니다.'}]
        if cmd == '판매정보':
            return message, ['!판매정보 (아이템 이름)', '해당 아이템을 판매하는 NPC 정보를 보여줍니다.\n 다른 호출법: !판매정보, !판매검색, !판매, !교환정보, !교환검색, !교환', '', '',
                             {'name': '아이템 이름', 'value': '아이템 이름은 띄어쓰기까지 정확해야 합니다.'},
                             {'name': '예시: !판매정보 하이 에테르', 'value': '하이 에테르의 판매 정보를 보여줍니다.'},
                             {'name': '정보 제공', 'value': '타르토맛 타르트 ([ff14.tar.to](https://ff14.tar.to))'}]