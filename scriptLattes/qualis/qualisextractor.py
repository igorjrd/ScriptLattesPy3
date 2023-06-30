#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import codecs
import logging
import urllib.request, urllib.error, urllib.parse
import pickle
from html.parser import HTMLParser
import datetime

import requests
from lxml import etree
import pandas as pd


logger = logging.getLogger(__name__)

# converts a string to a integer if the string is a integer, else returns None
def str2int(string):
    if string == None:
        return None
    try:
        return int(string)
    except ValueError:
        return None


def getvalue(attrs):
    for attr in attrs:
        if attr[0] == 'value':
            return attr[1]
    return None


class QualisExtractor(object):
    # Constructor
    def __init__(self, read_from_cache=True, arquivo_areas_qualis=None, data_file_path=None):
        self.read_from_cache = read_from_cache  # extrair online ou offline ?

        # self.publicacao = {}  #{'titulo': {'area': 'estrato'}}
        # self.issn = {}  #{'issn': {'area': 'estrato'}}
        self.qualis_data_frame = pd.DataFrame(columns=['issn', 'periodico', 'area', 'estrato'])
        self.areas             = []
        self.areas_to_extract  = []
        self.areas_last_update = {}
        self.dtnow             = datetime.datetime.now()
        self.update_time       = 15

        if arquivo_areas_qualis:
            self.parse_areas_file(arquivo_areas_qualis)

        if data_file_path:
            self.load_data(data_file_path)

        # self.init_session()
        self.initialized = True #False
        self.url2        = None

    def get_areas(self, document):
        tree = etree.HTML(document)
        self.areas = []
        select = tree.xpath("//select[@id='consultaDocumentosAreaForm:somAreaAvaliacao']/option")
        for option in select:
            self.areas.append(str2int(option.get("value")), option.text.strip())

    def init_session(self):
        """
        Sao necessarias tres requisicoes iniciais para que se chegue a pagina
        que exibe a avaliacao dos artigos.
        """
        if not self.initialized:
            url_base = "http://qualis.capes.gov.br/webqualis/"
            acesso_inicial = requests.get(url_base + 'principal.seam')
            jid = acesso_inicial.cookies['JSESSIONID']
            logger.info('Iniciando sessão qualis. ID da Sessão: {}'.format(jid))
            url1 = url_base + "publico/pesquisaPublicaClassificacao.seam;jsessionid=" + jid + "?conversationPropagation=begin"
            req1 = urllib.request.Request(url1)
            arq1 = urllib.request.urlopen(req1)

            self.url2 = url_base + "publico/pesquisaPublicaClassificacao.seam;jsessionid=" + jid
            self.initialized = True

        return self.url2

        # "http://qualis.capes.gov.br/webqualis/publico/pesquisaPublicaClassificacao.seam"
        # FIXME: verificar se este código ainda é útil
        # if not self.online:
        # req2 = urllib2.Request(self.url2,
        # # 'AJAXREQUEST=_viewRoot&consultaPublicaClassificacaoForm=consultaPublicaClassificacaoForm&consultaPublicaClassificacaoForm%3Aissn=&javax.faces.ViewState=j_id2&consultaPublicaClassificacaoForm%3Aj_id192=consultaPublicaClassificacaoForm%3Aj_id192')
        # 'AJAXREQUEST=_viewRoot&consultaPublicaClassificacaoForm=consultaPublicaClassificacaoForm&consultaPublicaClassificacaoForm%3Aissn=&javax.faces.ViewState=j_id2')
        # # 'AJAXREQUEST=_viewRoot&consultaPublicaClassificacaoForm=consultaPublicaClassificacaoForm&consultaPublicaClassificacaoForm%3Aissn=&javax.faces.ViewState=j_id4&consultaPublicaClassificacaoForm%3Aj_id195=consultaPublicaClassificacaoForm%3Aj_id195')
        # # "AJAXREQUEST=_viewRoot&consultaPublicaClassificacaoForm=consultaPublicaClassificacaoForm&consultaPublicaClassificacaoForm"%"3Aissn=&javax.faces.ViewState=j_id6&consultaPublicaClassificacaoForm"%"3Aj_id195=consultaPublicaClassificacaoForm"%"3Aj_id195&"
        # arq2 = urllib2.urlopen(req2)
        #     # get all qualis areas
        #     document = arq2.read()
        #     self.get_areas(document)
        #     req3 = urllib2.Request(self.url2,
        #                            'consultaPublicaClassificacaoForm=consultaPublicaClassificacaoForm&consultaPublicaClassificacaoForm%3AsomAreaAvaliacao=0&consultaPublicaClassificacaoForm%3AsomEstrato=org.jboss.seam.ui.NoSelectionConverter.noSelectionValue&consultaPublicaClassificacaoForm%3AbtnPesquisarTituloPorArea=Pesquisar&javax.faces.ViewState=j_id2')
        #     # 'consultaPublicaClassificacaoForm=consultaPublicaClassificacaoForm&consultaPublicaClassificacaoForm%3AsomAreaAvaliacao=23&consultaPublicaClassificacaoForm%3AsomEstrato=org.jboss.seam.ui.NoSelectionConverter.noSelectionValue&consultaPublicaClassificacaoForm%3AbtnPesquisarTituloPorArea=Pesquisar&javax.faces.ViewState=j_id4')
        #     arq3 = urllib2.urlopen(req3)
        #     a3 = arq3.read()

    def parse_areas_file(self, afile):
        '''
        Formato do arquivo:
        Nome da area 1
        Nome da area 2
        ...
        '''
        if not afile:
            return False
        f = codecs.open(afile, 'r', 'utf-8')
        lines = f.read()
        f.close()
        lines = lines.split('\n')
        areas = []
        for line in lines:
            val = line.partition('#')[0]
            val = val.strip()
            if val:
                self.areas_to_extract.append(val.upper())
        return True

    def should_update_area(self, area):
        lupdt = self.areas_last_update.get(area)
        if lupdt == None: return True
        dtbtween = self.dtnow - lupdt
        if dtbtween.days > self.update_time: return True
        return False

    def extract_qualis(self):
        # FIXME: método só é chamado para extração offline, mas então não deveria ficar acessando a internet. Rever.
        for area in self.areas_to_extract:
            if not self.should_update_area(area):
                logger.info('Qualis da area {} atualizado!'.format(self.areas[area][1]))
                continue

            self.areas_last_update[area] = self.dtnow
            scroller = 1
            more = 1
            # FIXME: armazenar mapeamento do nome da área para seu código, e utilizar o código nas URLs abaixo.
            reqn = urllib.request.Request(self.url2,
                                   'consultaPublicaClassificacaoForm=consultaPublicaClassificacaoForm&consultaPublicaClassificacaoForm%3AsomAreaAvaliacao=' + str(
                                       area) + '&consultaPublicaClassificacaoForm%3AsomEstrato=org.jboss.seam.ui.NoSelectionConverter.noSelectionValue&consultaPublicaClassificacaoForm%3AbtnPesquisarTituloPorArea=Pesquisar&javax.faces.ViewState=j_id2')

            arqn = urllib.request.urlopen(reqn)
            data = []
            logger.info('Qualis da area {} desatualizado!'.format(area))
            logger.info('Extraindo qualis da area: {}'.format(area))
            while more == 1:
                reqn = urllib.request.Request(self.url2,
                                       'AJAXREQUEST=_viewRoot&consultaPublicaClassificacaoForm=consultaPublicaClassificacaoForm&consultaPublicaClassificacaoForm%3AsomAreaAvaliacao=' + str(
                                           area) + '&consultaPublicaClassificacaoForm%3AsomEstrato=org.jboss.seam.ui.NoSelectionConverter.noSelectionValue&javax.faces.ViewState=j_id3&ajaxSingle=consultaPublicaClassificacaoForm%3AscrollerArea&consultaPublicaClassificacaoForm%3AscrollerArea=' + str(
                                           scroller) + '&AJAX%3AEVENTS_COUNT=1&')

                # arqn = urllib2.urlopen (reqn)
                tries = 10
                for i in range(tries):
                    try:
                        arqn = urllib.request.urlopen(reqn)
                        break  # success
                    except urllib.error.URLError as err:
                        logger.warning('Erro extraindo qualis. Tentando novamente.')
                        # continue
                        # if not isinstance(err.reason, socket.timeout):
                        # raise "Non timeout error occurried while loading page." # propagate non-timeout errors
                        # else: # all ntries failed
                        # raise err # re-raise the last timeout error
                    if i == tries:
                        logger.warning(
                            'Não foi possível extrair qualis mesmo após {} tentativas. Desistindo.'.format(tries))
                        break

                more = self.parse_content(arqn)  # FIXME: funcionamento de parse_content mudou
                scroller += 1

    def load_data(self, filename='data'):
        try:
            logger.debug('Carregando dados Qualis do arquivo \'{}\''.format(filename))
            f = open(filename, 'r')
            data = pickle.load(f)
            # self.issn = data[0]
            # self.publicacao = data[1]
            # self.areas = data[2]
            # self.areas_last_update = data[3]
            self.qualis_data_frame = data[0]
            self.areas = data[1]
            self.areas_last_update = data[2]
            f.close()
            return True
        except:
            return False

    def save_data(self, filename='data'):
        logger.debug('Salvando dados Qualis no arquivo \'{}\''.format(filename))
        f = open(filename, 'w')
        # data = (self.issn, self.publicacao, self.areas, self.areas_last_update)
        data = (self.qualis_data_frame, self.areas, self.areas_last_update)
        pickle.dump(data, f)
        f.close()

    def get_area_by_name(self, name):
        for i in self.areas:
            if i[1].upper() == name.upper():
                return i
        return None

    def get_area_by_cod(self, cod):
        for i in self.areas:
            if i[0] == cod:
                return i

    @staticmethod
    def read_url(req, tries=10, issn=None):
        arqn = None
        for i in range(tries):
            try:
                arqn = urllib.request.urlopen(req)
                break  # success
            except urllib.error.URLError as err:
                logger.warning('Erro extraindo Qualis do ISSN {}. Tentando novamente.'.format(issn))
            if i == tries - 1:
                logger.warning(
                    'Não foi possível extrair Qualis do ISSN {} mesmo após {} tentativas. Desistindo.'.format(
                        issn, tries))
                break
        html_document = arqn.read()
        return html_document

    def extract_online_qualis_by_issn(self, issn):
        """
        Extrai a classificação Qualis do dado ISSN. O sistema webqualis da CAPES é acessado e os HTMLs retornados são
        parseados.

        Para poupar tempo no acesso, uma mesma sessão é aproveitada nas chamadas seguintes a este método (ver
        self.init_session()). Entretanto, há um comportamento bizarro do sistema webqualis, que acontece mesmo
        navegando-se por um browser: quando um novo ISSN é pesquisado, a tabela de resultados é iniciada na página
        em que a tabela dos resultados anteriores estava. Por isso há um tratamento especial abaixo para lidar com
        o caso de ISSNs com várias páginas de resultado.

        :param issn: string do issn a ser extraido (deve estar no formato 1234-5678)
        :return: um pandas DataFrame com as colunas [issn, nome periodico, area, estrato]
        """
        qualis_data_frame = pd.DataFrame(columns=['issn', 'periodico', 'area', 'estrato'])

        # self.initialized = False
        url = self.init_session()
        # url0 = url + "?conversationPropagation=begin"
        # urllib2.urlopen(urllib2.Request(url0))

        req = urllib.request.Request(url,
                              'consultaPublicaClassificacaoForm=consultaPublicaClassificacaoForm&consultaPublicaClassificacaoForm%3Aissn=' + str(
                                  issn) + '&consultaPublicaClassificacaoForm%3AbtnPesquisarISSN=Pesquisar&javax.faces.ViewState=j_id2')
        html_document = self.read_url(req)
        partial_data_frame = self.parse_content(html_document)
        qualis_data_frame = qualis_data_frame.append(partial_data_frame, ignore_index=True)

        pages = self.other_pages(html_document)
        for scroller in pages:
            req = urllib.request.Request(url,
                                  'AJAXREQUEST=_viewRoot&consultaPublicaClassificacaoForm=consultaPublicaClassificacaoForm&consultaPublicaClassificacaoForm%3Aissn=' + str(
                                      issn) + '&javax.faces.ViewState=j_id3&ajaxSingle=consultaPublicaClassificacaoForm%3Adatascroller1&consultaPublicaClassificacaoForm%3Adatascroller1=' + str(
                                      scroller) + '&AJAX%3AEVENTS_COUNT=1&')
            html_document = self.read_url(req)
            partial_data_frame = self.parse_content(html_document)
            qualis_data_frame = qualis_data_frame.append(partial_data_frame, ignore_index=True)

        return qualis_data_frame

    def get_qualis_by_issn(self, issn):
        """
        Retorna Qualis do respectivo ISSN. Restringe as areas se elas tiverem sido especificadas (ver parse_areas_file).

        NOTA: ISSN tem que estar no formato XXXX-YYYY
        """
        logger.info('Extraindo qualis do ISSN {}...'.format(issn))

        issn_data = self.qualis_data_frame[self.qualis_data_frame['issn'] == issn]
        if issn_data.empty or not self.read_from_cache:
            issn_data = self.extract_online_qualis_by_issn(issn)
            if issn_data.empty:
                # adiciona o issn informando que não há Qualis associado; poupará requisições futuras
                issn_data.loc[0] = [issn, None, None, None]
            if not self.read_from_cache:
                # Descarta ISSN antigo da cache
                self.qualis_data_frame = self.qualis_data_frame[self.qualis_data_frame['issn'] != issn]
            self.qualis_data_frame = self.qualis_data_frame.append(issn_data, ignore_index=True)

        issn_data = issn_data.dropna()  # descarta ISSN's sem Qualis

        if self.areas_to_extract:
            issn_data = issn_data[issn_data['area'].isin(self.areas_to_extract)]

        # XXX: note que se houver chaves repetidas, só o último valor é salvo. Neste caso aqui não há problema, já que cada área só tem uma avaliação.
        qualis = dict(list(zip(issn_data['area'], issn_data['estrato'])))

        print("----------------")
        print(qualis)
        print("----------------")

        return qualis

    def extract_online_qualis_by_title(self, journal_title):
        """
        Extrai a classificação Qualis do dado periódico a partir do seu nome. O sistema webqualis da CAPES é acessado e
        os HTMLs retornados são parseados.

        Para poupar tempo no acesso, uma mesma sessão é aproveitada nas chamadas seguintes a este método (ver
        self.init_session()). Entretanto, há um comportamento bizarro do sistema webqualis, que acontece mesmo
        navegando-se por um browser: quando um novo ISSN é pesquisado, a tabela de resultados é iniciada na página
        em que a tabela dos resultados anteriores estava. Por isso há um tratamento especial abaixo para lidar com
        o caso de ISSNs com várias páginas de resultado.

        :param issn: string do issn a ser extraido (deve estar no formato 1234-5678)
        :return: um pandas DataFrame com as colunas [issn, nome periodico, area, estrato]
        """
        qualis_data_frame = pd.DataFrame(columns=['issn', 'periodico', 'area', 'estrato'])

        # self.initialized = False
        url = self.init_session()
        # url0 = url + "?conversationPropagation=begin"
        # urllib2.urlopen(urllib2.Request(url0))

        req = urllib.request.Request(url,
                              'consultaPublicaClassificacaoForm=consultaPublicaClassificacaoForm&consultaPublicaClassificacaoForm%3Atitulo=' +
                              str(journal_title) +
                              '&consultaPublicaClassificacaoForm%3AbtnPesquisarTitulo=Pesquisar&javax.faces.ViewState=j_id2')
        html_document = self.read_url(req)
        partial_data_frame = self.parse_content(html_document)
        qualis_data_frame = qualis_data_frame.append(partial_data_frame, ignore_index=True)

        pages = self.other_pages(html_document)
        for scroller in pages:
            req = urllib.request.Request(url,
                                  'AJAXREQUEST=_viewRoot&consultaPublicaClassificacaoForm=consultaPublicaClassificacaoForm&consultaPublicaClassificacaoForm%3Atitulo=' +
                                  str(journal_title) +
                                  '&javax.faces.ViewState=j_id3&ajaxSingle=consultaPublicaClassificacaoForm%3Adatascroller2&consultaPublicaClassificacaoForm%3Adatascroller2=' +
                                  str(scroller) + '&AJAX%3AEVENTS_COUNT=1&')
            html_document = self.read_url(req)
            partial_data_frame = self.parse_content(html_document)
            qualis_data_frame = qualis_data_frame.append(partial_data_frame, ignore_index=True)

        return qualis_data_frame

    def get_qualis_by_title(self, journal_title):
        """
        Retorna o Qualis a partir do nome do periódico. Restringe as areas se elas tiverem sido especificadas (ver parse_areas_file).
        """
        logger.info('Extraindo qualis do periódico "{}"...'.format(journal_title))

        data = self.qualis_data_frame[self.qualis_data_frame['periodico'] == journal_title]
        if data.empty or not self.read_from_cache:
            data = self.extract_online_qualis_by_title(journal_title)
            if data.empty:
                # adiciona o issn informando que não há Qualis associado; poupará requisições futuras
                data.loc[0] = [None, journal_title, None, None]
            else:
                if not self.read_from_cache:
                    # Descarta ISSN antigo da cache
                    if data['issn']:
                        issn = data['issn'].unique()[0]
                        self.qualis_data_frame = self.qualis_data_frame[self.qualis_data_frame['issn'] != issn]
                    else:
                        self.qualis_data_frame = self.qualis_data_frame[self.qualis_data_frame['periodico'] != journal_title]
            self.qualis_data_frame = self.qualis_data_frame.append(data, ignore_index=True)

        # data = data.dropna()  # descarta ISSN's sem Qualis

        if self.areas_to_extract:
            data = data[data['area'].isin(self.areas_to_extract)]

        # XXX: note que se houver chaves repetidas, só o último valor é salvo. Neste caso aqui não há problema, já que cada área só tem uma avaliação.
        qualis = dict(list(zip(data['area'], data['estrato'])))

        print(('###################', qualis))

        return qualis

        # qualis = self.publicacoes.get(name)
        '''if qualis != None: return qualis,1
        else:
            iqualis = -1
            r = 0
            pkeys = self.publicacoes.keys()
            for i in xrange(0,pkeys):
                nr = similaridade_entre_cadeias( name, pkeys[i], qualis=True)
                if nr > r:
                    r = nr
                    iqualis = i
            if r > 0:
                return self.publicacoes.get(pkeys[iqualis]),0
        '''
        return None

    @staticmethod
    def has_more_content(html_document):
        tree = etree.HTML(html_document)

        # /html/body/div[3]/div[4]/form/table/tbody/tr[2]/td/table/tbody/tr/td/div[2]/div/div/table/tbody/tr/td[11]
        last_bts = tree.xpath("//table[@id='consultaPublicaClassificacaoForm:datascroller1_table']/tbody/tr/td")
        # print etree.tostring(last_bts)
        # se encontrar um botao com onclick='page:last', entao ainda tem paginas
        if len(last_bts) > 0:
            onclick = last_bts[-1].get("onclick")
            if onclick is not None and onclick.find('{\'page\': \'last\'}') != -1:
                return True
        return False

    @staticmethod
    def other_pages(html_document):
        tree = etree.HTML(html_document)
        inactive_page_buttons = tree.xpath("//table[@id='consultaPublicaClassificacaoForm:datascroller1_table']/tbody/tr/td[@class='rich-datascr-inact ']")  # espaço em branco na classe
        return [button.text for button in inactive_page_buttons]

    @staticmethod
    def parse_content(document):
        """
        Process a html page containing qualis data
        Input parameters:
            document: the document to be parsed
        Output parameters:
            issn: a dictionary containing the parsed ISSNs and Qualis
            journal: a dictionary containing the parsed journal names and Qualis
        Return:
            1 if more pages exist
            0 otherwise
        """

        data_frame  = pd.DataFrame(columns=['issn', 'periodico', 'area', 'estrato'])
        tree        = etree.HTML(document)
        table_lines = tree.xpath("//table[@id='consultaPublicaClassificacaoForm:listaVeiculosIssn']/tbody/tr")

        for tr in table_lines:
            print(tr)

            line = []
            for td in tr:
                line.append(HTMLParser().unescape(td.text.strip()))
            issn_q, journal_q, estrato_q, area_q, classif_q = line

            if not issn_q or not journal_q:
                continue

            data_frame.loc[len(data_frame)] = [issn_q, journal_q, area_q, estrato_q]

        return data_frame
