# STAColletionsForMetadata

# Script para Geração de Metadados XML a Partir de Coleções STAC

## Descrição

Este repositório contém um script Python que automatiza a criação de arquivos de metadados XML no padrão **ISO 19115/19139**. Os metadados são gerados a partir de coleções STAC (SpatioTemporal Asset Catalog) disponibilizadas em um endpoint STAC.

### Principais Funcionalidades

- **Requisições a um servidor STAC**: O script acessa o endpoint fornecido para obter informações das coleções disponíveis.
- **Extração de Metadados**:
  - Identificador da coleção.
  - Descrição, título e palavras-chave.
  - Extensão espacial (caixa delimitadora geográfica).
  - Extensão temporal (período de validade dos dados).
  - Restrições de uso e licenciamento.
  - Recursos online associados (e.g., links para os dados ou serviços).
  - Formatos de dados disponíveis (e.g., PNG, GeoTIFF, COG).
- **Atualização de Template XML**: Utiliza um arquivo XML base para preencher os metadados extraídos de cada coleção.
- **Geração de Arquivos XML**: Cria arquivos separados para cada coleção no formato ISO 19115/19139.

## Diagrama de Fluxo de Dados

![image](https://github.com/user-attachments/assets/fe36dc28-2830-495d-8290-6e28a301c9b9)

## Estrutura do Repositório

- `MetadataTemplateSTAC.xml`: Arquivo de template base utilizado para gerar os metadados.
- `script.py`: Script principal contendo a lógica de extração e geração de metadados.
- `output_xml_files/`: Diretório onde os arquivos XML gerados são salvos.
- `README.md`: Este arquivo.

## Requisitos

- Python 3.8 ou superior.
- Bibliotecas Python:
  - `requests`: Para fazer requisições HTTP ao endpoint STAC.
  - `xml.etree.ElementTree`: Para manipulação de arquivos XML.
  - `os`: Para manipulação de arquivos e diretórios.
  - `datetime`: Para lidar com formatação de datas.

## Como Usar

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/seu-repositorio.git
   cd seu-repositorio
   ```
   
2. Instale as dependências:
   ```bash
   pip install requests 
   ```
3. Atualize a variável collections_url no script com o endpoint do servidor STAC desejado.
4. Certifique-se de que o arquivo MetadataTemplateSTAC.xml está configurado corretamente no mesmo diretório do script.
5. Execute o script:
   ```bash
   python script.py
   ```
6. Os arquivos XML serão salvos no diretório output_xml_files.

### Exemplos de Uso
- Metadados para mosaicos Landsat: Endpoint utilizado: https://data.inpe.br/bdc/stac/v1/collections.

- Extração de formatos de dados: Identifica formatos como PNG, GeoTIFF, e COG (Cloud Optimized GeoTIFF) presentes nos itens da coleção.
