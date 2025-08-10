import requests
import json
from vgdb_general import smart_http_request
import shapely.wkt
import geojson


def parse_layerjson(layerjson, geom_type):
    result_gj = {
        "type": "FeatureCollection",
        "features": []
    }
    # https://gist.github.com/drmalex07/5a54fc4f1db06a66679e
    for jsonf in layerjson:
        g1 = shapely.wkt.loads(jsonf["geom"])        
        props = jsonf['fields']
        props['id'] = jsonf['id']
        feat = geojson.Feature(geometry=g1, properties=props)
        result_gj['features'].append(feat)
        pass
    if not result_gj["features"]:
        return None
    return result_gj


def download_khmao_json(layernames):
    with requests.Session() as s:
        url = "http://gis.crru.ru:8080/api/resource/153/webmap/display_config"
    
        status, result = smart_http_request(s, url=url)
        if status != 200:
            raise ValueError('Config file not downloaded')
        config = result.json()
        groups = [child for child in config["rootItem"]["children"] if child["type"] == 'group']
        for layername in layernames:
            layerconfig = None
            layerconfig = [layer for group in groups for layer in group["children"] if layer["label"].lower() == layername.lower()]
            # if not layerconfig:
            #     raise ValueError(f'Layer {layername} not found')
            if layerconfig:
                layerconfig = layerconfig[0]
                crscode = 0
                geom_type = 'unknown'
                url = f"http://gis.crru.ru:8080/api/resource/{layerconfig['layerId']}"
                status, result = smart_http_request(s, url=url)
                if status == 200:
                    layerdesc = result.json()
                    if layerdesc.get("vector_layer"):
                        crscode = layerdesc["vector_layer"]["srs"]["id"]
                        geom_type = layerdesc["vector_layer"]["geometry_type"]
                url = f"http://gis.crru.ru:8080/api/resource/{layerconfig['layerId']}/feature/"
                params = {
                    "geom": "true",
                    "extensions": "",
                    "dt_format": "iso",
                    "offset": "0",
                    "limit": "100000"
                }
                status, result = smart_http_request(s, url=url, params=params)
                if status == 200:
                    layerjson = result.json()
                    layergjson = parse_layerjson(layerjson, geom_type)
                    if layergjson:
                        with open(f"result/{layername}_{str(crscode)}.json", 'w', encoding='utf-8') as f:
                            json.dump(layergjson, f, ensure_ascii=False, indent=2)
                    
        

if __name__ == '__main__':
    download_khmao_json([
        'магистральные газопроводы',
        'магистральные нефтепроводы',
        'месторождения УВ',
        'Лицензии на геологическое изучение',
        'Лицензии на разведку и добычу',
        'Участки распределенного фонда недр'
    ])