from ..abstract_webtools import *
import random
operating_systems = ['Macintosh','Windows','Linux']
browsers = ['Firefox','Chrome','IceDragon','Waterfox','Gecko','Safari','MetaSr']
def get_itter(iter_input,itter_list):
    if not iter_input:
        return itter_list[0]
    if iter_input in itter_list:
        return iter_input
    iter_input_lower = iter_input.lower()
    for itter in itter_list:
        itter_lower = itter.lower()
        if iter_input_lower in itter_lower:
            return itter
    return itter_list[0]
def get_browser(browser=None):
    return get_itter(browser,browsers)
def get_operating_system(operating_system=None):
    return get_itter(operating_system,operating_systems)
class UserAgentManager:
    def __init__(self, operating_system=None, browser=None, version=None,user_agent=None):
        self.operating_system = get_operating_system(operating_system=operating_system)
        self.browser = get_browser(browser=browser)
        self.version = version or '42.0'
        self.user_agent = user_agent or self.get_user_agent()
        self.header = self.user_agent_header()
    @staticmethod
    def user_agent_db():
        from ..big_user_agent_list import big_user_agent_dict
        return big_user_agent_dict

    def get_user_agent(self):
        ua_db = self.user_agent_db()

        if self.operating_system and self.operating_system in ua_db:
            operating_system_db = ua_db[self.operating_system]
        else:
            operating_system_db = random.choice(list(ua_db.values()))

        if self.browser and self.browser in operating_system_db:
            browser_db = operating_system_db[self.browser]
        else:
            browser_db = random.choice(list(operating_system_db.values()))

        if self.version and self.version in browser_db:
            return browser_db[self.version]
        else:
            return random.choice(list(browser_db.values()))

    def user_agent_header(self):
        return {"user-agent": self.user_agent}
class UserAgentManagerSingleton:
    _instance = None
    @staticmethod
    def get_instance(user_agent=UserAgentManager().get_user_agent()[0]):
        if UserAgentManagerSingleton._instance is None:
            UserAgentManagerSingleton._instance = UserAgentManager(user_agent=user_agent)
        elif UserAgentManagerSingleton._instance.user_agent != user_agent:
            UserAgentManagerSingleton._instance = UserAgentManager(user_agent=user_agent)
        return UserAgentManagerSingleton._instance
