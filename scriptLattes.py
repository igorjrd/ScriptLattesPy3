#!/usr/bin/env python 
# encoding: utf-8
#
#  scriptLattes
#  Copyright http://scriptlattes.sourceforge.net/
#
#  Este programa é um software livre; você pode redistribui-lo e/ou 
#  modifica-lo dentro dos termos da Licença Pública Geral GNU como 
#  publicada pela Fundação do Software Livre (FSF); na versão 2 da 
#  Licença, ou (na sua opinião) qualquer versão.
#
#  Este programa é distribuído na esperança que possa ser util, 
#  mas SEM NENHUMA GARANTIA; sem uma garantia implicita de ADEQUAÇÂO a qualquer
#  MERCADO ou APLICAÇÃO EM PARTICULAR. Veja a
#  Licença Pública Geral GNU para maiores detalhes.
#
#  Você deve ter recebido uma cópia da Licença Pública Geral GNU
#  junto com este programa, se não, escreva para a Fundação do Software
#  Livre(FSF) Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#
#import logging
#import warnings
#import requests, BeautifulSoup  # required by QualisExtractor
#warnings.filterwarnings('ignore')

from scriptLattes.grupo import *
from scriptLattes.util import *

if 'win' in sys.platform.lower():
    os.environ['PATH'] += ";" + os.path.abspath(os.curdir + '\\Graphviz2.36\\bin')
# sys.stdout = OutputStream(sys.stdout, sys.stdout.encoding)
# sys.stderr = OutputStream(sys.stderr, sys.stdout.encoding)


def executar_scriptLattes(arquivoConfiguracao):
    # os.chdir( os.path.abspath(os.path.join(arquivoConfiguracao, os.pardir)))
    novoGrupo = Grupo(arquivoConfiguracao)
    novoGrupo.imprimirListaDeRotulos()
    novoGrupo.carregar_dados_temporarios_de_geolocalizacao()

    if criarDiretorio(novoGrupo.obterParametro('global-diretorio_de_saida')):
        novoGrupo.carregarDadosCVLattes() #obrigatorio
        novoGrupo.compilarListasDeItems() # obrigatorio
        novoGrupo.identificarQualisEmPublicacoes() # obrigatorio
        novoGrupo.calcularInternacionalizacao() # obrigatorio

        novoGrupo.gerarGrafosDeColaboracoes() # obrigatorio
        novoGrupo.gerarMapaDeGeolocalizacao() # obrigatorio
        novoGrupo.gerarPaginasWeb() # obrigatorio
        novoGrupo.gerarArquivosTemporarios() # obrigatorio

        novoGrupo.salvar_dados_temporarios_de_geolocalizacao()

        # copiar imagens e css
        copiarArquivos(novoGrupo.obterParametro('global-diretorio_de_saida'))

        # finalizando o processo
        #print '[AVISO] Quem vê \'Lattes\', não vê coração! B-)'
        #print '[AVISO] Por favor, cadastre-se na página: http://scriptlattes.sourceforge.net\n'
        print ('\n[PARA REFERENCIAR/CITAR ESTE SOFTWARE USE] \n\
    Jesus P. Mena-Chalco & Roberto M. Cesar-Jr.\n\
    scriptLattes: An open-source knowledge extraction system from the Lattes Platform.\n\
    Journal of the Brazilian Computer Society, vol.15, n.4, páginas 31-39, 2009.\n\
    http://dx.doi.org/10.1007/BF03194511\n\
    \nscriptLattes executado!\n')

        # para incluir a producao com colaboradores é necessário um novo chamado ao scriptLattes
        if (novoGrupo.obterParametro('relatorio-incluir_producao_com_colaboradores')):
            executar_scriptLattes( novoGrupo.obterParametro('global-diretorio_de_saida') + "/producao-com-colaboradores.config" )



if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(format='%(asctime)s - %(levelname)s (%(name)s) - %(message)s')
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')
    logging.root.setLevel(level=logging.INFO)
    logging.root.setLevel(level=logging.DEBUG)
    logger.info("Executando '{}'".format(' '.join(sys.argv)))

    executar_scriptLattes(sys.argv[1])