import os
import json
from .. import api, sv
from ..steamid_converter import is_steamid64, is_bungie_membershipid
from hoshino import logger

binds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "binds.json")
binds_info = ["uid", "membership_id", "membership_type", "display_name", "steam_id", "bungie_membership_id"]
binds_token = ["access_token", "access_token_expire", "refresh_token", "refresh_token_expire"]

serach_data = {} # 玩家搜索结果list,重启后清空,格式为 {uid:{gid:data}}

def get_search_data(uid:str, gid:str, index:str=0) -> dict:
    try:
        if index == "": index = 0
        if uid not in serach_data.keys(): raise Exception("你个憨批，得先使用【d2搜索玩家 昵称】进行搜索了啦")
        if gid not in serach_data[uid].keys(): raise Exception("你还没有在当前群进行过玩家搜索哦")
        if index not in serach_data[uid][gid].keys(): raise Exception(f"変態不審者さん、请输入正确的搜索结果序号...你输入的序号“{index}”是错的啦！")
        return serach_data[uid][gid][index]
    except Exception: raise

def load_binds() -> dict:
    binds = {}
    if os.path.exists(binds_path):
        with open(binds_path, "r", encoding='utf-8') as dump_f:
            try: binds = json.load(dump_f)
            except: raise Exception("fatal error: can't load binds.json")
    return binds
    
def save_binds(binds):
    with open(binds_path, "w", encoding='utf-8') as dump_f: json.dump(binds, dump_f, indent=4, ensure_ascii=False)

binds = load_binds()

def bind_user(uid:int, **kwargs):
    """
    :param kwargs: membership_id, membership_type, display_name, steam_id, bungie_membership_id, access_token, access_token_expire, refresh_token, refresh_token_expire
    """
    if str(uid) not in binds.keys(): binds[str(uid)] = {"info":{}, "token":{}}
    if "info" not in binds[str(uid)].keys(): binds[str(uid)]["info"] = {}
    if "token" not in binds[str(uid)].keys(): binds[str(uid)]["token"] = {}
    for i in kwargs:
        if i in binds_info: binds[str(uid)]["info"][i] = kwargs[i]
        if i in binds_token: binds[str(uid)]["token"][i] = kwargs[i]
    save_binds(binds)

async def search_player_from_steamid(steamid):
    resp = await api.callapi(api.get_membership_from_hard_linked_credential(steamid))
    msid = resp.data['membershipId']
    mstype = resp.data['membershipType']
    name = await get_displayname(msid, mstype)
    player_data = {}
    player_data['membershipType'] = mstype
    player_data['membershipId'] = msid
    player_data['displayName'] = name
    return player_data

async def search_player_from_username(username):
    resp = await api.callapi(api.search_destiny_player(username))
    data_ = []
    for i in resp.data:
        mstype = i["membershipType"]
        msid = i["membershipId"]
        name = i["displayName"]
        data_.append({"membershipType":mstype, "membershipId":msid, "displayName":name})
    return data_

async def get_displayname(msid, mstype):
    resp = await api.callapi(api.get_profile(msid, mstype, 100))
    try: return resp.data["profile"]["data"]["userInfo"]["displayName"]
    except KeyError: return None

@sv.on_prefix(("d2搜索玩家","d2玩家搜索"))
async def d2_user_search(bot, ev):
    name = ev.message.extract_plain_text().strip()
    uid = str(ev.user_id)
    gid = str(ev.group_id)
    data_ = await search_player_from_username(name)
    tmp = {}
    msg = ['请发送【d2绑定 序号】绑定你的游戏账号~\n序号为0则可省略\n']
    for idx, i in enumerate(data_):
        mstype = i['membershipType']
        platform = api.mstype_converter(mstype)
        name = i['displayName']
        msg.append(f"{idx}.用户名：{name}\n游戏平台：{platform}\n")
        tmp[idx] = i
    if uid not in serach_data.keys(): serach_data[uid] = {}
    if gid not in serach_data[uid].keys(): serach_data[uid][gid] = {}
    serach_data[uid][gid] = tmp
    msg.append('如果无法通过玩家昵称找到你的账号，请发送【d2登陆】或发送【d2绑定 steamid（加入码）】进行玩家绑定\n如果想进一步确认玩家信息，请发送【d2查看玩家 序号】查看上面的搜索结果详情')
    await bot.send(ev, '\n'.join(msg))

@sv.on_prefix(("d2查看玩家"))
async def d2_user_detail(bot, ev):
    # 可以直接从搜索结果里查看对应玩家的游戏时长等信息，以确定重名玩家
    pass


@sv.on_prefix(("d2绑定"))
async def d2_user_bind(bot, ev):
    ptext = ev.message.extract_plain_text().strip()
    uid = str(ev.user_id)
    gid = str(ev.group_id)
    if not ptext or ptext.isdigit() and len(ptext) <= 2: # if passed index num
        try: userdata = get_search_data(uid, gid, ptext)
        except Exception as e: 
            await bot.send(ev, f"绑定玩家出错，{e}", at_sender=True)
            return
    elif is_steamid64(ptext): userdata = await search_player_from_steamid(ptext)[0]
    #elif is_bungie_membershipid(ptext): userdata = await search_player_from_steamid(ptext)[0]
    try: 
        mstype = userdata["membershipType"]
        msid = userdata["membershipId"]
        name = userdata["displayName"]
        bind_user(int(uid), membership_id=msid, membership_type=mstype, display_name=name)
    except KeyError as e:
        logger.error(f"bind user failed: key error {e}, origin data is {userdata}")
        await bot.send(ev, f"绑定玩家失败，请重试或截图联系BOT管理员\norigin data: {userdata}", at_sender=True)
        return
    except Exception as e:
        logger.error(f"bind user failed: origin data is {userdata}")
        await bot.send(ev, f"绑定玩家失败，请重试或截图联系BOT管理员\norigin data: {userdata}", at_sender=True)
        return
    await bot.send(ev, f"已经帮変態さん绑定好用户名为【{name}】的玩家啦", at_sender=True)
