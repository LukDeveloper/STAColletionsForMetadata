import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime

# URL da coleção
collection_url = "https://data.inpe.br/bdc/stac/v1/collections/S2_L2A_BUNDLE-1"

# Requisição para obter os detalhes da coleção
response = requests.get(collection_url)
collection_data = response.json()

# Extração dos atributos necessários
title = collection_data.get("title", "Título não disponível")
description = collection_data.get("description", "Resumo não disponível")
keywords = collection_data.get("keywords", [])
restrictions = collection_data.get("license", "Restrições não disponíveis")
links = collection_data.get("links", [])
if len(links) > 4:
    license_info = {
        "title": links[4].get("title", "Título não disponível"),
        "href": links[4].get("href", "Link de licença não disponível")
    }
else:
    license_info = {
        "title": "Título não disponível",
        "href": "Link de licença não disponível"
    }

# Extração da caixa delimitadora geográfica (spatial_extent)
bbox = collection_data.get("extent", {}).get("spatial", {}).get("bbox", [])
# Verificação para garantir que bbox tenha exatamente 4 valores e conversão para float
if len(bbox) > 0 and len(bbox[0]) == 4:
    spatial_extent = [float(coord) for coord in bbox[0]]  # Conversão para float
else:
    spatial_extent = [0.0, 0.0, 0.0, 0.0]  # Valores padrão se não for possível extrair

# Extração da extensão temporal (temporal_extent)
temporal_interval = collection_data.get("extent", {}).get("temporal", {}).get("interval", [])
# Verificação para garantir que temporal_interval tenha exatamente 2 valores
if len(temporal_interval) > 0 and len(temporal_interval[0]) == 2:
    temporal_extent = [temporal_interval[0][0], temporal_interval[0][1]]  # Captura os valores de início e fim
else:
    temporal_extent = ['2000-01-01T00:00:00Z', '2100-01-01T00:00:00Z']  # Valores padrão

# Recurso online
links = collection_data.get("links", [])
online_resource = [link.get("href") for link in links if link.get("rel") == "self"]

# Caminho para Template XML ISO19115/19139
template_file = '/kaggle/input/templatecollection/templatestac.xml'
with open(template_file, 'r', encoding='utf-8') as file:
    xml_template = file.read()

# Definindo namespaces
namespaces = {
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gml': 'http://www.opengis.net/gml/3.2'
}

# Registrar os namespaces para evitar "ns0", "ns2", "ns3"
for prefix, uri in namespaces.items():
    ET.register_namespace(prefix, uri)

# Função para formatar datas no padrão YYYY-MM-DD
def format_date(date_str):
    try:
        # Tenta converter a data e remover o tempo, deixando apenas o formato YYYY-MM-DD
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
    except ValueError:
        # Em caso de erro de parsing, retorna a string original (se já estiver no formato correto)
        return date_str
    
# Retorna a URL da overview (imagem PNG)    
def get_first_png_url(stac_collection_url):
    # Concatenando "/items" ao final da URL da coleção STAC
    stac_items_url = stac_collection_url.rstrip('/') + "/items"

    # Requisição para obter os itens da coleção
    response = requests.get(stac_items_url)
    items_data = response.json()

    # Variável para armazenar a URL da primeira imagem PNG encontrada
    first_png_url = None

    # Verificando os itens
    for item in items_data['features']:
        # Extraindo os assets do item
        assets = item['assets']

        # Verificando cada asset
        for asset_name, asset_info in assets.items():
            # Se o asset for do tipo PNG
            if asset_info['href'].endswith('.png'):
                first_png_url = asset_info['href']
                break  # Sai do loop se encontrar a primeira imagem PNG
        if first_png_url:
            break  # Sai do loop se encontrar a primeira imagem PNG

    # Retorna a URL da primeira imagem PNG encontrada ou uma mensagem de erro
    if first_png_url:
        return first_png_url
    else:
        return "Nenhuma imagem PNG encontrada."

# Função para substituir placeholders com dados reais
def update_xml_with_data(xml_template, data):
    tree = ET.ElementTree(ET.fromstring(xml_template))
    root = tree.getroot()

    # Adicionando valor para o "Título"
    title_elem = root.find('.//gmd:title/gco:CharacterString', namespaces)
    if title_elem is not None:
        title_elem.text = data.get('title', '')

    # Adicionando valor para "Resumo"
    abstract_elem = root.find('.//gmd:abstract/gco:CharacterString', namespaces)
    if abstract_elem is not None:
        abstract_elem.text = data.get('description', '')

    # Adicionando valor para "Palavras-chave"
    keywords_elems = root.findall('.//gmd:keyword/gco:CharacterString', namespaces)
    for i, keyword_elem in enumerate(keywords_elems):
        if i < len(data.get('keywords', [])):
            keyword_elem.text = data['keywords'][i]
        else:
            keyword_elem.text = ''
    
     # Adicionando valor para "Overview (URL da imagem)"
    overview = root.find('.//gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString', namespaces)
    if overview is not None:
        overview.text = get_first_png_url(collection_url)

    # Adicionando valor para "Restrições de Recursos"
    constraints_elem = root.find('.//gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:otherConstraints/gco:CharacterString', namespaces)
    if constraints_elem is not None:
        constraints_elem.text = f"{license_info['title']}: {license_info['href']}"

    # Adicionando caixa delimitadora geográfica
    bbox_elem = root.find('.//gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox', namespaces)
    if bbox_elem is not None and len(data.get('spatial_extent', [])) == 4:
        bbox_elem.find('gmd:westBoundLongitude/gco:Decimal', namespaces).text = str(data['spatial_extent'][0])
        bbox_elem.find('gmd:eastBoundLongitude/gco:Decimal', namespaces).text = str(data['spatial_extent'][2])
        bbox_elem.find('gmd:southBoundLatitude/gco:Decimal', namespaces).text = str(data['spatial_extent'][3])
        bbox_elem.find('gmd:northBoundLatitude/gco:Decimal', namespaces).text = str(data['spatial_extent'][1])

    # Adicionando extensão temporal corretamente dentro de gmd:EX_TemporalExtent
    temporal_elem = root.find('.//gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod', namespaces)
    if temporal_elem is not None:
        begin_elem = temporal_elem.find('gml:beginPosition', namespaces)
        end_elem = temporal_elem.find('gml:endPosition', namespaces)
        if begin_elem is not None and len(data.get('temporal_extent', [])) > 0:
            begin_elem.text = format_date(data['temporal_extent'][0])  # Formatar período de início
        if end_elem is not None and len(data.get('temporal_extent', [])) > 1:
            end_elem.text = format_date(data['temporal_extent'][1])  # Formatar período de fim

    # Adicionando recurso online
    online_elem = root.find('.//gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL', namespaces)
    if online_elem is not None and data.get('online_resource'):
        online_elem.text = data['online_resource'][0]

    return tree

# Diretório para salvar os arquivos XML de saída
output_dir = '/kaggle/working/output_xml_files'
os.makedirs(output_dir, exist_ok=True)

# Dados de exemplo
example_data = {
    'title': title,
    'description': description,
    'keywords': keywords,
    'restrictions': restrictions,
    'spatial_extent': spatial_extent,
    'temporal_extent': temporal_extent,
    'online_resource': online_resource
}

# Atualizar o template XML e salvar o arquivo
tree = update_xml_with_data(xml_template, example_data)
output_file = os.path.join(output_dir, 'collection_metadata.xml')
tree.write(output_file, encoding='UTF-8', xml_declaration=True)

print(f'Arquivo XML gerado: {output_file}')
