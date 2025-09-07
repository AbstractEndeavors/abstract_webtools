from abstract_utilities import *
import time
class DynamicRateLimiterManager:
    def __init__(self, service_name='ethereum'):
        self.services = {}
        self.service_name = service_name
        self.add_service(service_name)

    def add_service(self, service_name="default", low_limit=10, high_limit=30, limit_epoch=60, starting_tokens=10, epoch_cycle_adjustment=True):
        if service_name in self.services:
            print(f"Service {service_name} already exists!")
            return
        self.services[service_name] = DynamicRateLimiter(low_limit=low_limit, high_limit=high_limit, limit_epoch=limit_epoch, starting_tokens=starting_tokens, epoch_cycle_adjustment=epoch_cycle_adjustment)

    def request(self, request_url, service_name=None):
        service_name = service_name or self.service_name
        if service_name not in self.services:
            self.add_service(service_name)

        limiter = self.services[service_name]

        while True:
            if limiter.request():
                response = requests.get(request_url)  # Actual request
                if response.status_code == 200:
                    limiter.request_tracker(True)
                    return response.json()
                elif response.status_code == 429:
                    limiter.request_tracker(False)
                    print(f"Rate limited by {service_name}. Adjusting limit and retrying...")
                    time.sleep(limiter.get_sleep()["current_sleep"])
                else:
                    print(f"Unexpected response: {response.status_code}. Message: {response.text}")
                    return None
            else:
                print(f"Rate limit reached for {service_name}. Waiting for the next epoch...")
                time.sleep(limiter.get_sleep()["current_sleep"])

    def log_request(self, service_name, success):
        print(f"[{service_name}] Request {'succeeded' if success else 'denied'}. Current tokens: {self.services[service_name].get_current_tokens()}")

class DynamicRateLimiter:
    def __init__(self, low_limit, high_limit, limit_epoch, starting_tokens=None,epoch_cycle_adjustment:int=None):
        self.low_limit = low_limit
        self.high_limit = high_limit
        self.limit_epoch = limit_epoch  # in seconds
        self.request_status_json = {"succesful":[],"unsuccesful":[],"last_requested":get_time_stamp(),"first_requested":get_time_stamp(),"epoch_left":self.limit_epoch,"last_fail":get_time_stamp(),"count_since_fail":0}
        self.current_limit = starting_tokens or low_limit  # Default to high_limit if starting_tokens isn't provided
        self.epoch_cycle_adjustment = epoch_cycle_adjustment
        # Additional attributes for tracking adjustment logic
        self.last_adjusted_time = get_time_stamp()
        self.successful_epochs_since_last_adjustment = 0
        self.request_count_in_current_epoch = 0

    def _refill_tokens(self):
        time_since_last_request = get_time_stamp() - self.request_status_json["last_requested"]
        new_tokens = (time_since_last_request / self.limit_epoch) * self.current_limit
        self.tokens = min(self.current_limit, self.get_current_tokens())
    def request_tracker(self,success):
        if success:
            self.request_status_json["succesful"].append(get_time_stamp())
        else:
            self.request_status_json["unsuccesful"].append(get_time_stamp())
            self.request_status_json["last_fail"]=get_time_stamp()
            self.request_status_json["count_since_fail"]=0
            self.adjust_limit()
        self.request_status_json["last_requested"]=get_time_stamp()
    def calculate_tokens(self):
        successful = []
        for each in self.request_status_json["succesful"]:
            if (get_time_stamp() - each)<self.limit_epoch:
                successful.append(each)
        self.request_status_json["succesful"]=successful
        unsuccessful = []
        for each in self.request_status_json["unsuccesful"]:
            if (get_time_stamp() - each)<self.limit_epoch:
                unsuccessful.append(each)
        self.request_status_json["unsuccesful"]=unsuccessful
        if len(successful)==0 and len(unsuccessful)==0:
            pass
        elif len(successful)!=0 and len(unsuccessful)==0:
            self.request_status_json["first_requested"] = successful[0]
        elif len(successful)==0 and len(unsuccessful)!=0:
            self.request_status_json["first_requested"] = unsuccessful[0]
        else:
            self.request_status_json["first_requested"] = min(unsuccessful[0],successful[0])
        self.request_status_json["epoch_left"]=self.limit_epoch-(self.request_status_json["last_requested"]-self.request_status_json["first_requested"])
        
        return self.request_status_json
    def get_current_tokens(self):
        self.request_status_json = self.calculate_tokens()
        total_requests = len(self.request_status_json["succesful"])+len(self.request_status_json["unsuccesful"])
        return max(0,self.current_limit-total_requests)
    def get_sleep(self):
        self.request_status_json = self.calculate_tokens()
        self.request_status_json["current_sleep"]=self.request_status_json["epoch_left"]/max(1,self.get_current_tokens())
        return self.request_status_json
    def request(self):
        self._refill_tokens()
        if self.tokens > 0:
            return True  # The request can be made
        else:
            if self.tokens == 0:
                self.request_status_json["count_since_fail"]+=1
                if self.epoch_cycle_adjustment != None:
                    if self.request_status_json["count_since_fail"] >=self.epoch_cycle_adjustment:
                        self.current_limit=min(self.current_limit+1,self.high_limit)
            return False  # The request cannot be made
    def _adjust_limit(self):
        current_time = get_time_stamp()
        if current_time - self.last_adjusted_time >= self.limit_epoch:
            if len(self.clear_epoch()["succesful"]) >= self.tokens:
                # We hit the rate limit this epoch, decrease our limit
                self.tokens = max(1, self.tokens - 1)
            else:
                self.successful_epochs_since_last_adjustment += 1
                if self.successful_epochs_since_last_adjustment >= 5:
                    # We've had 5 successful epochs, increase our limit
                    self.current_limit = min(self.high_limit, self.tokens + 1)
                    self.successful_epochs_since_last_adjustment = 0
            
            # Reset our counters for the new epoch
            self.last_adjusted_time = current_time
            self.request_count_in_current_epoch = 0
    def adjust_limit(self):
        # Set the tokens to succesful requests_made - 1
        self.tokens = len(self.calculate_tokens()["succesful"])

        # Adjust the high_limit
        self.current_limit = self.tokens

        # Log the adjustment
        print(f"Adjusted tokens to: {self.tokens} and high_limit to: {self.current_limit}")
class DynamicRateLimiterManagerSingleton:
    _instance = None
    @staticmethod
    def get_instance(service_name="default", low_limit=10, high_limit=30, limit_epoch=60,starting_tokens=10,epoch_cycle_adjustment=True):
        if DynamicRateLimiterManagerSingleton._instance is None:
            DynamicRateLimiterManagerSingleton._instance = DynamicRateLimiterManager(service_name=service_name, low_limit=low_limit, high_limit=limit_epoch, limit_epoch=60,starting_tokens=starting_tokens,epoch_cycle_adjustment=epoch_cycle_adjustment)
        return DynamicRateLimiterManagerSingleton._instance
