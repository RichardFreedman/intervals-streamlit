import os.path
import requests

MEI_GARAGE_ENDPOINT = 'https://meigarage.edirom.de/ege-webservice/Conversions/musicxml-partwise%3Atext%3Axml/musicxml-timewise%3Atext%3Axml/mei30%3Atext%3Axml/mei40%3Atext%3Axml/'

def convert(xml_loc, xml_filename, mei_garage_endpoint=MEI_GARAGE_ENDPOINT):
  mei_garage_endpoint = MEI_GARAGE_ENDPOINT if mei_garage_endpoint is None else mei_garage_endpoint
  xml = os.path.join(xml_loc, xml_filename)
  with open(xml, 'rb') as f:
    r = requests.post(mei_garage_endpoint, files={xml_filename: f})
    # if r.status_code != 200:
    #     raise
    r.encoding = "utf-8"
    return r.text
