import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime

# URL da coleção
collections_url = "https://data.inpe.br/bdc/stac/v1/collections"

# Requisição para obter a lista de coleções
response = requests.get(collections_url)
collections_data = response.json().get("collections", [])

# Caminho para Template XML ISO19115/19139
template_file = '/kaggle/input/templateatualizado/MetadataTemplateSTAC.xml'
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
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
    except ValueError:
        return date_str

# Função para obter a URL da primeira imagem PNG de uma coleção STAC
def get_first_png_url(stac_collection_url):
    # URL dos itens da coleção
    stac_items_url = stac_collection_url.rstrip('/') + "/items"

    # Requisição para obter os itens
    response = requests.get(stac_items_url)
    
    if response.status_code != 200:
        return "Erro ao acessar os itens da coleção"

    items_data = response.json().get('features', [])

    # Percorre os itens da coleção
    for item in items_data:
        # Verifica se há 'assets' no item
        assets = item.get('assets', {})
        
        # Itera sobre os assets para procurar por PNG
        for asset_info in assets.values():
            if asset_info.get('href', '').endswith('.png'):
                return asset_info['href']
    
    return "Nenhuma imagem PNG encontrada."

# Função para extrair formatos dos assets
def get_resource_formats(stac_collection_url):
    stac_items_url = stac_collection_url.rstrip('/') + "/items"
    response = requests.get(stac_items_url)
    
    if response.status_code != 200:
        return ["Erro ao acessar os itens da coleção"]

    items_data = response.json().get('features', [])
    
    formats = set()

    # Itera sobre os itens e assets para coletar os formatos
    for item in items_data:
        assets = item.get('assets', {})
        for asset_info in assets.values():
            asset_type = asset_info.get('type')
            if asset_type:
                formats.add(asset_type)

    return list(formats)

def process_collection(collection_data, stac_collection_url):
    print(f"Processando coleção: {collection_data.get('id', 'ID não disponível')}")
    
    # Extração dos atributos necessários
    title = collection_data.get("title", "Título não disponível")
    description = collection_data.get("description", "Resumo não disponível")
    keywords = collection_data.get("keywords", []) 
    collection_id = collection_data.get("id", "ID não disponível")
    print(f'Atualizando XML para a coleção: {collection_id}')
    
    # Licença e links
    links = collection_data.get("links", [])
    restrictions = collection_data.get("license", "Restrições não disponíveis")

    # Extraindo informações da licença de forma segura
    if len(links) > 4:
        license_info = {
            "title": links[4].get("title", "Licença não disponível"),
            "href": links[4].get("href", "Link de licença não disponível")
        }
    else:
        license_info = {
            "title": "Licença não disponível",
            "href": "Link de licença não disponível"
        }

    # Extração da caixa delimitadora geográfica (spatial_extent)
    bbox = collection_data.get("extent", {}).get("spatial", {}).get("bbox", [])
    spatial_extent = [float(coord) for coord in bbox[0]] if len(bbox) > 0 and len(bbox[0]) == 4 else [0.0, 0.0, 0.0, 0.0]

    # Extração da extensão temporal (temporal_extent)
    temporal_interval = collection_data.get("extent", {}).get("temporal", {}).get("interval", [])
    temporal_extent = [temporal_interval[0][0], temporal_interval[0][1]] if len(temporal_interval) > 0 and len(temporal_interval[0]) == 2 else ['2000-01-01T00:00:00Z', '2100-01-01T00:00:00Z']

    # Recurso online
    online_resource = [link.get("href") for link in links if link.get("rel") == "self"]

    # Obtenha os formatos de recursos
    formats = get_resource_formats(stac_collection_url)
    
    # Adicionando license_info ao exemplo de dados
    example_data = {
        'title': title,
        'description': description,
        'keywords': keywords,
        'restrictions': restrictions,
        'spatial_extent': spatial_extent,
        'temporal_extent': temporal_extent,
        'online_resource': online_resource,
        'collection_id': collection_id,
        'collection_url': stac_collection_url,
        'license_info': license_info,
        'formats': formats
    }
    
    tree = update_xml_with_data(xml_template, example_data)
    output_file = os.path.join(output_dir, f'{collection_id}_metadata.xml')
    tree.write(output_file, encoding='UTF-8', xml_declaration=True)

    print(f'Arquivo XML gerado: {output_file}')

# Função para substituir placeholders com dados reais
def update_xml_with_data(xml_template, data):
    tree = ET.ElementTree(ET.fromstring(xml_template))
    root = tree.getroot()

    try:
        file_identifier_elem = root.find('.//gmd:fileIdentifier/gco:CharacterString', namespaces)
        if file_identifier_elem is not None:
            file_identifier_elem.text = data.get('collection_id', '')
    
        # Adicionando valor para o "Título"
        title_elem = root.find('.//gmd:title/gco:CharacterString', namespaces)
        if title_elem is not None:
            title_elem.text = data.get('title', '')
    
        # Adicionando valor para "Resumo"
        abstract_elem = root.find('.//gmd:abstract/gco:CharacterString', namespaces)
        if abstract_elem is not None:
            abstract_elem.text = data.get('description', '')
    
        # Adicionando palavras-chave ao XML
        keywords_parent_elem = root.find('.//gmd:descriptiveKeywords/gmd:MD_Keywords', namespaces)
        
        # Verifica se a seção de palavras-chave já existe
        if keywords_parent_elem is not None:
            # Limpa as palavras-chave existentes (se necessário)
            for keyword_elem in keywords_parent_elem.findall('.//gmd:keyword', namespaces):
                keywords_parent_elem.remove(keyword_elem)  # Remover diretamente o elemento encontrado
        
            # Adiciona novas palavras-chave com base no input
            for keyword in data.get('keywords', []):
                new_keyword_elem = ET.SubElement(keywords_parent_elem, 'gmd:keyword')
                char_string_elem = ET.SubElement(new_keyword_elem, 'gco:CharacterString')
                char_string_elem.text = keyword
        
         # Adicionando valor para "Overview (URL da imagem)"
        overview = root.find('.//gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString', namespaces)
        if overview is not None:
            overview.text = get_first_png_url(data.get('collection_url', ''))
    
        # Adicionando valor para "Restrições de Recursos"
        constraints_elem = root.find('.//gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:otherConstraints/gco:CharacterString', namespaces)
        if constraints_elem is not None:
            constraints_elem.text = f"{data['license_info']['title']}: {data['license_info']['href']}"
    
        # Adicionando caixa delimitadora geográfica
        bbox_elem = root.find('.//gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox', namespaces)
        if bbox_elem is not None and len(data.get('spatial_extent', [])) == 4:
            bbox_elem.find('gmd:westBoundLongitude/gco:Decimal', namespaces).text = str(data['spatial_extent'][0])
            bbox_elem.find('gmd:eastBoundLongitude/gco:Decimal', namespaces).text = str(data['spatial_extent'][2])
            bbox_elem.find('gmd:southBoundLatitude/gco:Decimal', namespaces).text = str(data['spatial_extent'][3])
            bbox_elem.find('gmd:northBoundLatitude/gco:Decimal', namespaces).text = str(data['spatial_extent'][1])
    
        # Adicionar e Corrigir a estrutura do XML para o intervalo temporal
        temporal_elem = root.find('.//gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod', namespaces)
        if temporal_elem is not None:
            begin_elem = temporal_elem.find('gml:beginPosition', namespaces)
            end_elem = temporal_elem.find('gml:endPosition', namespaces)
            
            if begin_elem is not None and len(data.get('temporal_extent', [])) > 0:
                begin_elem.text = format_date(data['temporal_extent'][0])
            
            if end_elem is not None and len(data.get('temporal_extent', [])) > 1:
                end_elem.text = format_date(data['temporal_extent'][1])
    
        # Adicionando recurso online
        online_elems = root.findall('.//gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine', namespaces)
        
        if len(online_elems) > 1 and data.get('online_resource'):
            # Atualiza o segundo recurso online
            second_online_elem = online_elems[1]
            
            # Atualiza o link
            link_elem = second_online_elem.find('.//gmd:CI_OnlineResource/gmd:linkage/gmd:URL', namespaces)
            if link_elem is not None:
                link_elem.text = data['online_resource'][0]

            # Atualiza o protocolo
            protocol_elem = second_online_elem.find('.//gmd:CI_OnlineResource/gmd:protocol/gco:CharacterString', namespaces)
            if protocol_elem is not None:
                protocol_elem.text = "WWW:LINK-2.0-http--link"

            # Atualiza o título do recurso
            title_resource = second_online_elem.find('.//gmd:CI_OnlineResource/gmd:name/gco:CharacterString', namespaces)
            if title_resource is not None:
                title_resource.text = f'{data.get("title", "")} Collection'

            # Atualiza a descrição do recurso
            descript_resource = second_online_elem.find('.//gmd:CI_OnlineResource/gmd:description/gco:CharacterString', namespaces)
            if descript_resource is not None:
                descript_resource.text = f'End point to access INPE Spatio Temporal Asset Catalog (STAC) server, collection {data.get("collection_id", "")}'  # Adapte conforme necessário
    
        # Adicionando formatos ao XML
        distribution_format_elem = root.find('.//gmd:distributionFormat', namespaces)    
        for fmt in data.get('formats', []):
            md_format = ET.SubElement(distribution_format_elem, 'gmd:MD_Format')
            
            name_elem = ET.SubElement(md_format, 'gmd:name')
            char_string_elem = ET.SubElement(name_elem, 'gco:CharacterString')
            char_string_elem.text = fmt
            
            version_elem = ET.SubElement(md_format, 'gmd:version')
            char_string_elem_version = ET.SubElement(version_elem, 'gco:CharacterString')
            char_string_elem_version.set('gco:nilReason', 'unknown')

    except Exception as e:
        print(f"Erro ao atualizar o XML: {e}")

    return tree

# Diretório para salvar os arquivos XML de saída
output_dir = '/kaggle/working/output_xml_files'
os.makedirs(output_dir, exist_ok=True)

if collections_data:
    # Processar cada coleção e Construir a URL para a coleção
    for collection in collections_data:
        collection_url = collections_url.rstrip('/') + f'/{collection["id"]}'
        process_collection(collection, collection_url)
else:
    print("Nenhuma coleção encontrada.")
