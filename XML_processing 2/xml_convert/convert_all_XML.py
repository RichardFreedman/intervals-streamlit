import convertXML2MEI
import argparse
from os import listdir
import os.path

XML_LOC = '/Users/rfreedma/Documents/CRIM_Python/XML_processing/input'
XML_OUT = '/Users/rfreedma/Documents/CRIM_Python/XML_processing/output'

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Convert music xml to mei')
  parser.add_argument('--mei', default=XML_LOC, dest="xml", help="directory where MEI files are located")
  parser.add_argument('--output', default=XML_OUT, dest="output", help="output directory")
  parser.add_argument('--meigarage', default=None, dest="garage", help="MEI Garage endpoint")

  options = parser.parse_args()

  if not os.path.exists(options.output):
    os.makedirs(options.output)

  xml_files = [f for f in listdir(options.xml) if os.path.isfile(os.path.join(options.xml, f))]

  for xml_filename in xml_files:
    xml = os.path.join(options.xml, xml_filename)
    if (not os.path.exists(xml)):
      print('Could not locate ', xml)
      continue
    # Convert to MEI4 using meigarage.
    mei_v4 = convertXML2MEI.convert(options.xml, xml_filename, options.garage)
    with open(os.path.join(options.output, xml_filename), 'w') as output_file:
      output_file.write(mei_v4)
