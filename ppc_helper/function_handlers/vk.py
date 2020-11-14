import vk_api
import time
import os

APP_ID = int(os.environ['VK_APP_ID'])
CLIENT_SECRET = os.environ['VK_CLIENT_SECRET']
TOKEN = os.environ['VK_TOKEN']
SCOPE = int(os.environ['VK_SCOPE'])
API_VERSION = os.environ['VK_API_VERSION']

vk_session = vk_api.VkApi(app_id=APP_ID, client_secret=CLIENT_SECRET, api_version=API_VERSION, scope=SCOPE,
                          token=TOKEN)
vk = vk_session.get_api()
# data object: {data, dbm, bot, chat_id}


def vk_get_user_id_by_url(data):
    """
    Get vk profile info by urls
    """
    urls = data['data'] # urls
    urls = urls.replace(' ', '')
    sep = '\n' if '\n' in urls else ','
    urls = urls.split(sep)

    names = [s.split('/')[-1] for s in urls]
    r = vk.users.get(user_ids=','.join(names))
    header = ['id', 'first_name', 'last_name']
    response = [header]
    for user in r:
        row = [user['id'], user['first_name'], user['last_name']]
        response.append(row)
    return response


def get_members(group_url):
    group_id = group_url.split('/')[-1]
    members = []
    r = vk.groups.getMembers(group_id=group_id)
    members += r['items']
    count = r['count']
    offset = 0
    while count > 0:
        count -= 1000
        offset += 1000
        members += vk.groups.getMembers(group_id=group_id, offset=offset)['items']
    return members


def vk_get_common_groups_by_url(data, low_limit=50):
    """
    Get all groups of all members of the group at group_url and count intersections
    :param low_limit: integer; specifies group with which number of members should be counted
    :return: list of rows with header
    """
    group_url = data['data']
    users = get_members(group_url)
    output = {}
    for u in users:
        groups = []
        try:
            r = vk.groups.get(user_id=u, fields='members_count', extended=1)
        except Exception:
            #log?
            continue
        groups += r['items']
        count = r['count']
        offset = 0
        while count > 0:
            count -= 1000
            offset += 1000
            groups += vk.groups.get(user_id=u, fields='members_count', extended=1, offset=offset)['items']
        for g in groups:
            if 'members_count' not in g or g['members_count'] < low_limit:
                continue
            if g['id'] not in output:
                output[g['id']] = {'name': g['name'], 'type': g['type'], 'members_count': g['members_count'],
                                   'common_count': 1}
            else:
                output[g['id']]['common_count'] += 1
    result = [['group_id', 'name', 'type', 'members_count', 'common_count'],]
    for k, v in output.items():
        row = [k, v['name'], v['type'], v['members_count'], v['common_count']]
        result.append(row)
    return result

