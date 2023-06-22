import requests, re
from bs4 import BeautifulSoup as BS

def searchinput(inputs, query):
    for entry in inputs:
        if query in entry.get('name'):
            return True
    return False

def parse_relationship_opts(soup):

    #get viewstate
    viewstate = soup.find(id='javax.faces.ViewState').get('value')

    # get form elem
    form = soup.find('form', method='post')
    formid = form.get('id')

    options = []

    #get association list
    assocs = form.find_all('li')
    for assoc in assocs:

        # get assoc text
        assoclist = []
        spans = assoc.find_all('span')
        for span in spans:
            assoclist.append(span.text)
        assoctext = ' - '.join(assoclist)

        # build data to post
        onclick = assoc.find('a').get('onclick')
        data = ""
        onclicklist = re.split('{|}', onclick)
        for onclick in onclicklist:
            if 'vinculo' in onclick:
                data = onclick
        datadict = eval(('{' + data + "}"))
        datadict['javax.faces.ViewState'] = viewstate
        datadict[formid] = formid
        options.append([assoctext, datadict])

    return options


def sigaa_lookup(username, password, reloption):

    status = None
    s = requests.Session()

    html = s.get(url = "https://sigaa.ufrrj.br/sigaa/mobile/touch/public/principal.jsf")
    soup = BS(html.text, 'html.parser')
    viewstate = soup.find(id='javax.faces.ViewState').get('value')

    data = {'form-lista-public-index': 'form-lista-public-index',
            'javax.faces.ViewState': viewstate,
            'form-lista-public-index:acessar': 'form-lista-public-index:acessar'}
    html = s.post(url = "https://sigaa.ufrrj.br/sigaa/mobile/touch/public/principal.jsf", data = data)
    soup = BS(html.text, 'html.parser')
    viewstate = soup.find(id='javax.faces.ViewState').get('value')
    formuser = soup.find('input', type='text').get('name')
    formpass = soup.find('input', type='password').get('name')

    data = {'form-login': 'form-login',
            formuser: username,
            formpass: password,
            'form-login:entrar': 'Entrar',
            'javax.faces.ViewState': viewstate}
    html = s.post(url = "https://sigaa.ufrrj.br/sigaa/mobile/touch/login.jsf", data = data)
    if "rio e/ou senha inv" in html.text:
        return status, None

    soup = BS(html.text, 'html.parser')

    # verify and pass relationship page
    relationship = soup.find(id='vinculos')
    if relationship != None:
        if reloption == None:
            # get reloptions from 'vinculos' page
            reloptions = parse_relationship_opts(soup)
            # return relationship options to render relationship page
            status = 'relationship'
            return status, reloptions
        else:
            html = s.post(url = "https://sigaa.ufrrj.br/sigaa/mobile/touch/vinculos.jsf", data = reloption)
            soup = BS(html.text, 'html.parser')


    inputs = soup.find_all('input')
    userinfo = {}
    if searchinput(inputs, 'form-portal-docente'):
        status = 'ok'
        userinfo['function'] = 'docente';
        info = list(soup.find('form', id='form-portal-docente').find('fieldset').stripped_strings)
        userinfo['register'] = info[0]
        userinfo['name'] = info[-2]
        userinfo['relationship'] = info[-1]

    elif searchinput(inputs, 'form-portal-discente'):
        status = 'ok'
        userinfo['function'] = 'discente';
        info = list(soup.find('form', id='form-portal-discente').find('fieldset').stripped_strings)
        userinfo['register'] = info[0]
        userinfo['name'] = info[-2]
        userinfo['relationship'] = info[-1]

    else:
        status = 'error'
        # parse problem (new page?)
        # save html that could not be parsed for later analysis
        with open(username + '.html', 'w') as f:
            f.write(html.text)

    return status, userinfo
