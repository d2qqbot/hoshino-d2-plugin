from hoshino import logger, aiorequests
from . import root_path, headers, proxies

root_path = 'https://www.bungie.net/Platform'
headers = {"X-API-Key":'aff47ade61f643a19915148cfcfc6d7d'}
proxies = {'http': '127.0.0.1:7890','https': '127.0.0.1:7890'}

async def callapi(url, token=None):
    _headers = headers.copy()
    if token: _headers["Authorization"] = "Bearer " + token
    response = await aiorequests.get(url, headers = _headers, proxies=proxies, timeout=5)
    result = await response.json() if response.status_code == 200 else None
    return ResponseSummary(response.status_code, response.url, result)

class ResponseSummary:
    def __init__(self, status, url, result=None):
        self.status = status
        self.url = url
        self.data = None
        self.message = None
        self.error_code = None
        self.error_status = None
        self.exception = None
        if self.status == 200:
            self.message = result['Message']
            self.error_code = result['ErrorCode']
            self.error_status = result['ErrorStatus']
            if self.error_code == 1:
                try: 
                    self.data = result['Response']
                except Exception as e:
                    logger.error("ResponseSummary: 200 status and error_code 1, but there was no result['Response']")
                    logger.error(f"Exception: {e}.\nType: {e.__class__.__name__}")
                    self.exception = e.__class__.__name__
            else: logger.error(f'No data returned for url: {self.url}.\n {self.error_code} was the error code with status 200.')
        else: logger.error(f'Request failed for url: {self.url}.\n.Status: {self.status}')
  
    def __repr__(self):
        """What will be displayed/printed for the class instance."""
        disp_header =       "<" + self.__class__.__name__ + " instance>\n"
        disp_data =         ".data: " + str(self.data) + "\n"
        disp_url =          ".url: " + str(self.url) + "\n"
        disp_message =      ".message: " + str(self.message) + "\n"
        disp_status =       ".status: " + str(self.status) + "\n"
        disp_error_code =   ".error_code: " + str(self.error_code) + "\n"
        disp_error_status = ".error_status: " + str(self.error_status) + "\n"
        disp_exception =    ".exception: " + str(self.exception)
        return disp_header + disp_data + disp_url + disp_message + \
               disp_status + disp_error_code + disp_error_status + disp_exception

"""
BungieMembershipType
None: 0
TigerXbox: 1
TigerPsn: 2
TigerSteam: 3
TigerBlizzard: 4
TigerStadia: 5
TigerDemon: 10
BungieNext: 254
All: -1
"""

def search_destiny_player(displayName, membershipType=-1):
    """
    通过用户名查找玩家, 返回membershipType, membershipId, displayName
    """
    return f"{root_path}/Destiny2/SearchDestinyPlayer/{membershipType}/{displayName}"

def get_linked_profiles(membershipId, membershipType=-1, getAllMemberships=False):
    """
    通过bungieid查找玩家, 有隐私限制, 需要auth
    """
    return f"{root_path}/Destiny2/{membershipType}/Profile/{membershipId}/LinkedProfiles/?getAllMemberships={getAllMemberships}"

def get_memberships_by_id(membershipId, membershipType=-1):
    """
    通过bungieid查找玩家
    """
    return f"{root_path}/User/GetMembershipsById/{membershipId}/{membershipType}"

def get_membership_from_hard_linked_credential(credential, crType='SteamId'):
    """
    通过steamid查找玩家
    """
    return f"{root_path}/User/GetMembershipFromHardLinkedCredential/{crType}/{credential}"

def get_memberships_for_current_user():
    """
    oauth直接查找玩家
    """
    return f"{root_path}/User/GetMembershipsForCurrentUser/"

def get_profile(destinyMembershipId, membershipType, components=100):
    """
    :param components: enum
    None: 0
    Profiles: 100
    VendorReceipts: 101
    ProfileInventories: 102
    ProfileCurrencies: 103
    ProfileProgression: 104
    PlatformSilver: 105
    Characters: 200
    CharacterInventories: 201
    CharacterProgressions: 202
    CharacterRenderData: 203
    CharacterActivities: 204
    CharacterEquipment: 205
    ItemInstances: 300
    ItemObjectives: 301
    ItemPerks: 302
    ItemRenderData: 303
    ItemStats: 304
    ItemSockets: 305
    ItemTalentGrids: 306
    ItemCommonData: 307
    ItemPlugStates: 308
    ItemPlugObjectives: 309
    ItemReusablePlugs: 310
    Vendors: 400
    VendorCategories: 401
    VendorSales: 402
    Kiosks: 500
    CurrencyLookups: 600
    PresentationNodes: 700
    Collectibles: 800
    Records: 900
    Transitory: 1000
    Metrics: 1100
    """
    return f"{root_path}/Destiny2/{membershipType}/Profile/{destinyMembershipId}/?components={components}"

def mstype_converter(membershipType:int):
    if isinstance(membershipType, str) and membershipType.isdigit(): membershipType = int(membershipType)
    if not isinstance(membershipType, int): raise Exception("type error")
    membershiptypes = {1:'Xbox', 2:'Psn', 3:'Steam', 4:'Blizzard', 5:'Stadia'}
    try: return membershiptypes[membershipType]
    except Exception: return 'unknown'