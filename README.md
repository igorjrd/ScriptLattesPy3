# ScriptLattes (Python 3)

Este repositório disponibiliza uma versão do [ScriptLattes](https://scriptlattes.sourceforge.net/) compatível com python 3. As adaptações foram realizadas utilizando [2to3](https://docs.python.org/3/library/2to3.html) e algumas refatorações manuais de código. Deve se observar que não estão aplicadas manutenções de códigos, depreciação de features ou novas implementações, de forma que o código mantém alta fidelidade à implementação original (com exceção da adaptação de métodos depreciados e atualização de dependências).

O ScriptLattes é uma ferramenta que permite a geração de uma página web com os relatórios de produção de um grupo de pesquisa a partir das informações dispostas nos [Currículos Lattes](https://lattes.cnpq.br/) dos membros componentes do grupo.

## Requisitos e instalação
A atual versão foi testada apenas em sistema Linux (em acordo com a compatibilidade do scriptLattes original) e python 3.10. Portanto, as instruções a seguir são válidas para sistema Linux.

Para download da ferramenta, pode se utilizar a opção "Download ZIP" ou utilizar `git clone` no repositório.

Dentre as dependências de sistema, deve ser instalado o tidy, para isso, execute:

`apt install tidy`

Para instalação das dependências python, recomenda-se a criação de um ambiente virtual (como venv ou conda). As dependências python podem ser instaladas com:

`pip install -r requirements.txt`

## Observações

- Após a implementação de sistema de captcha na plataforma Lattes, o download automático de currículos não vem sendo executado com sucesso. Deve ser feito download manual e organização dos currículos html no diretório de cache definido na configuração do usuário;
- Não houve sucesso na validação do uso da interface gráfica disponível no script `scriptLattesGUI.py` após o port para python 3;
- Podem haver recursos com testagem mínima após o port, nestes casos recomenda-se abrir uma Issue reportando o bug.

## Instruções
As demais instruções para uso da ferramenta estão disponíveis na [página web do ScriptLattes](https://scriptlattes.sourceforge.net/) e no arquivo README.txt na raiz deste repositório.

## Créditos
Aqui consta a lista de idealizadores e colaboradores responsáveis pela codificação/implementação e melhorias/modificações e correções:

### Idealização

    Jesús P. Mena-Chalco (UFABC)
    Roberto M. Cesar-Jr (USP)


### Versão Python

    Cátia Nascimento (UFRGS)
    Celina Maki Takemura (EMBRAPA)
    Christina von Flach G. Chavez (UFBA)
    Evelyn Perez Cervantes (IME-USP)
    Fabio N. Kepler (UNIPAMPA)
    Helena Caseli (UFSCar)
    Richard W. Valdivia (UNIFESP)
    Wonder Alexandre Luz Alves (UNINOVE).

### Versão Perl

    Carlos Morais de Oliveira Filho (IME-USP)
    Christina von Flach G. Chavez (UFBA)
    Luc Quoniam (Université Du Sud Toulon Var)
    Renato Novais (UFBA)
    Silvio de Paula (USP)

### Adaptação para Python 3

    Igor Jordão Marques (INTM-UFPE)