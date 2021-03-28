import hoshino
from hoshino import aiorequests
import nonebot
from nonebot import on_command
import json
import time
import hashlib
import base64
from Crypto.Cipher import AES
from quart import Quart, request, Blueprint

from .bind import bind_user
from .. import api

login_pool = []
bot = nonebot.get_bot()

class BungieOauth:
    async def get_token(self):
        authorization = "Basic " + str(base64.b64encode(bytes(f"{config.OAUTH_CLIENT_ID}:{config.OAUTH_CLIENT_SECRET}",encoding="utf-8")),encoding="utf-8")
        headers = {"Authorization":authorization, "Content-Type":"application/x-www-form-urlencoded"}
        body = f"grant_type=authorization_code&client_id={config.OAUTH_CLIENT_ID}&code={self.code}&client_secret={config.OAUTH_CLIENT_SECRET}"
        url = "https://www.bungie.net/platform/app/oauth/token/"
        resp = await aiorequests.post(url, headers=headers, data=body, timeout=5, proxies=config.PROXIES)
        data = await resp.json()
        ts = int(time.time())
        self.token = data["access_token"]
        self.expire = ts + data["expires_in"]
        self.refresh_token = data["refresh_token"]
        self.refresh_expire = ts + data["refresh_expires_in"]
        self.bungie_membership_id = data["membership_id"]
    async def __call__(self, code, state):
        self.code = code
        global login_pool
        try:
            if state not in login_pool: raise Exception("login task has not been created or already finished")
            await self.get_token()
            login_pool.remove(state)
            tmp = unpack_state(state)
            uid, gid = tmp[1], tmp[2]
            resp = await api.callapi(api.get_memberships_for_current_user(), token=self.token)
            data_ = resp.data
            msid = data_["primaryMembershipId"]
            name = mstype = None
            for i in data_["destinyMemberships"]:
                if i["membershipId"] == msid: 
                    name = i["displayName"]
                    mstype = i["membershipType"]
            bind_user(int(uid), membership_id=msid, membership_type=mstype, display_name=name, access_token=self.token, access_token_expire=self.refresh_token, refresh_token=self.refresh_expire, refresh_token_expire=self.refresh_expire, bungie_membership_id=self.bungie_membership_id)
            msg = f"已经帮変態さん绑定好用户名为【{name}】的玩家啦"
            if gid == "0": await bot.send_private_msg(user_id=uid, message=msg)
            else: await bot.send_group_msg(group_id=gid, message=msg)
        except Exception as e: raise Exception(f"bungie oauth failed, {e}")

@on_command("d2登陆", only_to_me=False)
async def d2_login(session):
    global login_pool
    sinfo = await bot.get_login_info()
    sid = str(sinfo["user_id"])
    uid = str(session.event.user_id)
    gid = str(session.event.group_id) if session.event.detail_type == 'group' else "0"
    state = creat_state(sid, uid, gid)
    login_pool.append(state)
    url = f"https://www.bungie.net/zh-chs/oauth/authorize?client_id={config.OAUTH_CLIENT_ID}&response_type=code&state={state}"
    msg = f"访问下方链接进行Bungie账户绑定\n{url}\n若无法访问请科学上网"
    await session.finish(msg,at_sender=True)

pdtext = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16).encode()

def encrypt(text):
    mode = AES.MODE_CBC
    vi = b'yNxOePejvuIKnj3P'
    key = b'ZpEKCiqsj8VxblSEHSs0FlaOVkz0DsmM'
    cryptor=AES.new(key,mode, vi)
    ss1 = pdtext(text.encode())
    plain_text  = cryptor.encrypt(ss1)
    return str(base64.urlsafe_b64encode(plain_text), encoding="utf-8")

def decrypt(b64text) -> tuple:
    encrypted = base64.urlsafe_b64decode(b64text)
    mode = AES.MODE_CBC
    vi = b'yNxOePejvuIKnj3P'
    key = b'ZpEKCiqsj8VxblSEHSs0FlaOVkz0DsmM'
    cryptor = AES.new(key, mode, vi)
    plain_text = str(cryptor.decrypt(encrypted), encoding="utf-8")
    return plain_text

def creat_state(sid:str, uid:str, gid:str): # botQQ, 用户QQ, 群号
    ts = str(int(time.time()))
    return encrypt(":".join([sid, uid, gid, ts]))

def unpack_state(decrypted):
    try:
        t = decrypt(decrypted).split(":")
        if len(t) != 4: raise Exception("length of list wrong")
        sid = t[0]
        uid = t[1]
        gid = t[2]
        ts = t[3][:10] # remove padding
        return (sid, uid, gid, ts)
    except Exception: raise

destiny = Blueprint("destiny", __name__, url_prefix="/destiny")
bot = nonebot.get_bot()
app = bot.server_app
config = hoshino.config.destiny2.destiny2_config
oauth = BungieOauth()

@destiny.route('/login/callback/', methods=['GET']) 
async def get_code():
    code = request.args.get('code')
    state = request.args.get('state')
    try: 
        await oauth(code, state)
        return "success!"
    except Exception as e: return str(e)

app.register_blueprint(destiny)