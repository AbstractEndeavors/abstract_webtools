from abstract_gui import make_component,sg
import inspect
import re
from . import UserAgentManager,UrlManager,SafeRequest,SoupManager,LinkManager,CipherManager,requests,ssl,BeautifulSoup,HTTPAdapter,PoolManager,ssl_
window = None

def get_attrs(values):
  tags_js={'tag':[],'attribute':[],'input':[]}
  for each in ['-SOUP_TAG-','-SOUP_ATTRIBUTE-','-SOUP_ATTRIBUTE_1-','-SOUP_ATTRIBUTE_2-']:
    if values[each[:-1]+'_BOOL-'] == True:
      for types in ['tag','attribute']:
        if types in each.lower():
          tags_js[types].append(values[each])
  input_val = values['-SOUP_VALUES_INPUT-']
  if input_val == '':
    tags_js['input']=None
  else:
    tags_js['input']= input_val
  if tags_js['tag']==[]:
    tags_js['tag']=None if match.group(1) else None
  else:
    tags_js['tag']=tags_js['tag'][0]
  if tags_js['attribute']==[]:
    tags_js['attribute']=None
  else:
    tags_js['attribute']=tags_js['attribute'][0]
  return tags_js
def get_user_agent_manager(user_agent=None):
  return UserAgentManager(user_agent=user_agent)
def get_cipher_list():
  return CipherManager().get_default_ciphers()
def get_parse_type_choices():
    return ['html.parser', 'lxml', 'html5lib']
def expandable(size:tuple=(None,None)):
    return {"size": size,"resizable": True,"scrollable": True,"auto_size_text": True,"expand_x":True,"expand_y": True}
def change_glob(var:any,val:any):
    globals()[var]=val
    return val
def get_parse_type_choices():
    bs4_module = inspect.getmodule(BeautifulSoup)
    docstring = bs4_module.__builtins__
    start_index = docstring.find("parse_types")
    end_index = docstring.find(")", start_index)
    choices_text = docstring[start_index:end_index]
    choices = [choice.strip() for choice in choices_text.split(",")]
    return choices
def get_browsers():
    return 'Chrome,Firefox,Safari,Microsoft Edge,Internet Explorer,Opera'.split(',')
def get_user_agents():
    from .big_user_agent_list import big_user_agent_list
    return big_user_agent_list
def create_user_agent(user_agent:str=get_user_agents()[0]):
    return {"user-agent": user_agent}
def get_operating_systems():
  return ['Windows NT 10.0','Macintosh; Intel Mac OS X 10_15_7','Linux','Android','iOS']
def create_columns(ls,i,k):
    if float(i)%float(k)==float(0.00) and i != 0:
        lsN = list(ls[:-k])
        lsN.append(list(ls[-k:]))
        ls = lsN
    return ls
def get_cypher_checks():
    ciphers_list = get_cipher_list()
    ls=[[[sg.Text('CIPHERS: ')],sg.Multiline('',key='-CIPHERS_OUTPUT-', size=(80, 5), disabled=False)]]
    for k,cipher in enumerate(ciphers_list):
        ls.append(sg.Checkbox(cipher,key=cipher,default=True,enable_events=True))
        ls = create_columns(ls,k,5)
    return ls
def get_bs4_options():
    bs4_options = [
        'BeautifulSoup',
        'Tag',
        'NavigableString',
        'Comment',
        'ResultSet',
        'SoupStrainer',
        'CData'
    ]
    descriptions = [
        'The main BeautifulSoup class used for parsing HTML.',
        'Represents an HTML tag.',
        'Represents a string within an HTML document.',
        'Represents an HTML comment.',
        'Represents a collection of tags found during a search.',
        'Allows parsing only a specific subset of the HTML document.',
        'Represents a CDATA section within an XML document.'
    ]
    return list(zip(bs4_options, descriptions))
def get_multi_line(args):
    return make_component("Multiline",**args,**expandable())
def get_gpt_layout(url):
    # Add a dropdown for selecting BeautifulSoup parsing capabilities
    parse_type_choices = ['html.parser', 'lxml', 'html5lib']
    make_component("theme",'LightGrey1')
    layout = [[sg.Text('URL:', size=(8, 1)), sg.Input(url, key='-URL-',enable_events=True),sg.Text('status:'),sg.Text('200',key="-STATUS_CODE-")
               ,sg.Text(f'success: {url} is valid',key="-URL_WARNING-"),sg.Button('Grab URL',key='-GRAB_URL-',visible=True)],
        [sg.Checkbox('Custom User-Agent', default=False, key='-CUSTOMUA-', enable_events=True)],
        [sg.Text('User-Agent:', size=(8, 1)), sg.Combo(get_user_agents(), default_value='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36', key='-USERAGENT-', disabled=False)],
        [get_cypher_checks()],
        [sg.Button('Grab URL'), sg.Button('Action'),sg.Button('Get All Text')],
        [sg.Text('Parsing Capabilities:', size=(15, 1)), sg.DropDown(parse_type_choices, default_value='html.parser', key='-parse_type-',enable_events=True)],
        [get_multi_line({"key":'-SOURCECODE-'})],
        [sg.Text('find soup:'),[[sg.Checkbox('',default=True,key='-SOUP_TAG_BOOL-',enable_events=True),sg.Combo([], size=(15, 1),key='-SOUP_TAG-',enable_events=True)],
                                [sg.Checkbox('',default=False,key='-SOUP_ATTRIBUTE_BOOL-',enable_events=True),sg.Combo([], size=(15, 1),key='-SOUP_ATTRIBUTE-',enable_events=True)],
                                [sg.Checkbox('',default=False,key='-SOUP_ATTRIBUTE_1_BOOL-',enable_events=True),sg.Combo([], size=(15, 1),key='-SOUP_ATTRIBUTE_1-',enable_events=True)],
                                [sg.Checkbox('',default=False,key='-SOUP_ATTRIBUTE_2_BOOL-',enable_events=True),sg.Combo([], size=(15, 1),key='-SOUP_ATTRIBUTE_2-',enable_events=True)],
                                sg.Input(key='-SOUP_VALUES_INPUT-'), sg.Button('get soup'),sg.Button('all soup'),sg.Button('Send Soup')]],
        [get_multi_line({"key":"-FIND_ALL_OUTPUT-"})]]
    return layout
def get_selected_cipher_list():
  ls = []
  ciphers_list = get_cipher_list()
  event, values = window.read()
  for cipher in ciphers_list:
      if values[cipher] == True:
          ls.append(cipher)
  return ls
def update_status(window,warn,warn_url,response_code,valid):
    window['-URL-'].update(value=warn_url)
    window['-STATUS_CODE-'].update(value=response_code)
    window["-URL_WARNING-"].update(value=f"{warn} : {warn_url} is {valid}")
def process_url(window,values):
    response_code=False
    temp_mgr=None
    warn='warning'
    valid='invalid'
    warn_url = values['-URL-']
    if warn_url=='' or warn_url == None:
      update_status(window,warn,warn_url,response_code,valid)
      return False
    temp_url=UrlManager(url=warn_url).url
    if temp_url:
      valid='valid'
      response_code = SafeRequest(url=temp_mgr).response.status_code
      warn = 'success'
      warn_url = temp_mgr
      update_status(window,warn,warn_url,response_code,valid)
      return temp_mgr
    update_status(window,warn,warn_url,response_code,valid)
    return False
def update_url(url_manager,request_manager,soup_manager,link_manager,values,cipher_list=get_cipher_list(),user_agent=get_user_agents()[0]):
      ciphers = CipherManager(cipher_list=cipher_list).ciphers_string
      request_manager = SafeRequest(url_manager=url_manager,ciphers=ciphers,user_agent=get_user_agents()[0])
      if request_manager.source_code:
        soup_manager= SoupManager(url_manager=url_manager,request_manager=request_manager)
        link_manager= LinkManager(url_manager=url_manager,request_manager=request_manager,soup_manager=soup_manager)
        window['-URL-'].update(value=url_manager.url)
        window['-CIPHERS_OUTPUT-'].update(value=request_manager.ciphers)
        return update_source_code(url_manager,request_manager,soup_manager,link_manager,values)
      else:
        return url_manager,request_manager,soup_manager,link_manager
def update_source_code(url_manager,request_manager,soup_manager,link_manager,values):
    parse_type = values['-parse_type-']
    if parse_type != soup_manager.parse_type:
      soup_manager.update_parse_type(parse_type=parse_type)
    all_tags=soup_manager.get_all_tags_and_attribute_names()
    window['-SOURCECODE-'].update(value=soup_manager.soup)
    if values['-SOUP_TAG-'] != all_tags['tags']:
      window['-SOUP_TAG-'].update(values=all_tags['tags'],value=all_tags['tags'][0])
    if values['-SOUP_ATTRIBUTE-'] != all_tags['attributes']:
      window['-SOUP_ATTRIBUTE-'].update(values=all_tags['attributes'],value=all_tags['attributes'][0])
      window['-SOUP_ATTRIBUTE_1-'].update(values=all_tags['attributes'],value=all_tags['attributes'][0])
      window['-SOUP_ATTRIBUTE_2-'].update(values=all_tags['attributes'],value=all_tags['attributes'][0])
      return url_manager,request_manager,soup_manager,link_manager
def url_grabber_while(window,initial_url="www.example.com"):
    return_data=None
    url_grab = False
    url_manager=UrlManager(url=initial_url)
    request_manager = SafeRequest(url_manager=url_manager)
    soup_manager= SoupManager(url_manager=url_manager,request_manager=request_manager)
    link_manager= LinkManager(url_manager=url_manager,request_manager=request_manager,soup_manager=soup_manager)
    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        if event=='-GRAB_URL-' or not url_grab:
          url=values['-URL-']
          if UrlManager(url=url).url:
            if url != url_manager.url or url == initial_url:
              url_manager = UrlManager(url=url)
              
              url_manager,request_manager,soup_manager,link_manager=update_url(url_manager=url_manager,request_manager=request_manager,soup_manager=soup_manager,link_manager=link_manager,values=values)
              window['-URL-'].update(value=url_manager.url)
              url_grab=True
        if event == 'get soup':
            tags_js = get_attrs(values)
            all_desired=soup_manager.find_tags_by_attributes(tag=tags_js['tag'], attr=tags_js['attribute'],attr_values=tags_js['input'])
            window['-FIND_ALL_OUTPUT-'].update(value=all_desired)
        if event == '-CUSTOMUA-':
            window['-SOURCECODE-'].update(disabled=values['-CUSTOMUA-'])
            if not values['-CUSTOMUA-']:
                window['-USERAGENT-'].update(value=user_agent_manager.user_agent_header)
                window['-USERAGENT-'].update(disabled=True)
            else:
                window['-USERAGENT-'].update(disabled=False)
        if event=='Get All Text':
            window['-FIND_ALL_OUTPUT-'].update(value=soup_manager.extract_text_sections())
        if event == 'Action':
            parse_type = values['-parse_type-']
            if parse_type != soup_manager.parse_type:
              soup_manager.update_parse_type(parse_type=parse_type)
            window['-SOURCECODE-'].update(value=soup_manager.soup)
        elif event == 'Send Soup':
          return_data = values['-FIND_ALL_OUTPUT-']
          break
    window.close()
    return return_data
def url_grabber_component(url=None):
    if url==None:
      url = "www.example.com"
    globals()['window'] = make_component('Window','URL Grabber', layout=get_gpt_layout(url),**expandable())
    return url_grabber_while(window,initial_url=url)

