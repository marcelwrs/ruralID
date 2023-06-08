import requests
from bs4 import BeautifulSoup as BS

def searchinput(inputs, query):
    for entry in inputs:
        if query in entry.get('name'):
            return True
    return False

def sigaa_lookup(username, password):

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
        return None

    # TODO: verify and pass association page

    soup = BS(html.text, 'html.parser')
    inputs = soup.find_all('input')
    userinfo = {}
    if searchinput(inputs, 'form-portal-docente'):
        userinfo['function'] = 'docente';
        info = list(soup.find('form', id='form-portal-docente').find('fieldset').stripped_strings)
        userinfo['register'] = info[0]
        userinfo['name'] = info[1]
        userinfo['association'] = info[2]

    elif searchinput(inputs, 'form-portal-discente'):
        userinfo['function'] = 'discente';
        info = list(soup.find('form', id='form-portal-discente').find('fieldset').stripped_strings)
        userinfo['register'] = info[0]
        userinfo['name'] = info[1]
        userinfo['association'] = info[2]

    else:
        # parse problem (new page?)
        # save html that could not be parsed for later analysis
        with open(username + '.html', 'w') as f:
            f.write(html.text)

    return userinfo
