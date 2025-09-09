# userAgentManager
import random

operating_systems = ['Macintosh','Windows','Linux']
browsers = ['Firefox','Chrome','IceDragon','Waterfox','Gecko','Safari','MetaSr']

def _pick(val, options):
    if not val: return options[0]
    if val in options: return val
    l = val.lower()
    for o in options:
        if l in o.lower():
            return o
    return options[0]

class UserAgentManager:
    def __init__(self, operating_system=None, browser=None, version=None, user_agent=None):
        self.operating_system = _pick(operating_system, operating_systems)
        self.browser = _pick(browser, browsers)
        self.version = version or '42.0'
        self.user_agent = user_agent or self.get_user_agent()
        self.header = {"user-agent": self.user_agent}

    @staticmethod
    def user_agent_db():
        from ..big_user_agent_list import big_user_agent_dict
        return big_user_agent_dict

    def get_user_agent(self):
        ua_db = self.user_agent_db()
        os_db = ua_db.get(self.operating_system) or random.choice(list(ua_db.values()))
        br_db = os_db.get(self.browser) or random.choice(list(os_db.values()))
        if self.version in br_db:
            return br_db[self.version]
        return random.choice(list(br_db.values()))

class UserAgentManagerSingleton:
    _instance = None

    @staticmethod
    def get_instance(**kwargs):
        ua = kwargs.get("user_agent")
        if UserAgentManagerSingleton._instance is None:
            UserAgentManagerSingleton._instance = UserAgentManager(**kwargs)
        else:
            # rebuild if user_agent explicitly changed
            inst = UserAgentManagerSingleton._instance
            if ua and ua != inst.user_agent:
                UserAgentManagerSingleton._instance = UserAgentManager(**kwargs)
        return UserAgentManagerSingleton._instance
