import logging
import requests
from pyhelpers import tools, grobid_mapping
tools.setup_logging(file_name="extractor.log")
import config as cfg
from lxml import etree
from six import text_type
import os

# mdocker pull lfoppiano/grobid:0.4.1-SNAPSHOT
# https://grobid.readthedocs.io/en/latest/Grobid-docker/
# https://github.com/kennknowles/python-jsonpath-rw


class TextExtraction:

  def __init__(self, booktitles, journals):

    # The booktitles are located in the config.py
    # If you are interested in specific conference just add it there
    #self.booktitles = cfg.booktitles
    #self.journals = cfg.journals

    if booktitles is None:
      # GET THE VENUES WE LIKE from config.py
      self.booktitles = cfg.booktitles
      print('Conference of Interest: {}'.format(cfg.booktitles))
    else:
      self.booktitles = booktitles
      print('Conference of Interest: {}'.format(self.booktitles))

    if journals is None:
      # GET THE VENUES WE LIKE from config.py
      self.journals = cfg.journals
      print('Journals of Interest: {}'.format(cfg.journals))
    else:
      self.journals = journals
      print('Journals of Interest: {}'.format(self.journals))

    for booktitle in self.booktitles:
      print("Processing booktitle: {}".format(booktitle))
      # {'$and': [{'booktitle': 'ESWC'}, {'content.chapters': {'$exists': True}}]}
      # mongo_search_string = {'content.chapters': {'$exists': False}}
      mongo_search_string = {'$and': [{'booktitle': booktitle}, {'content.chapters': {'$exists': False}}]}
      self.process_papers(mongo_search_string)

    for journal in self.journals:
      print("Processing journal: {}".format(journal))
      # {'$and': [{'booktitle': 'ESWC'}, {'content.chapters': {'$exists': True}}]}
      # mongo_search_string = {'content.chapters': {'$exists': False}}
      mongo_search_string = {'$and': [{'journal': journal}, {'content.chapters': {'$exists': False}}]}
      self.process_papers(mongo_search_string)

  def get_grobid_xml(self, paper_id):
      """
      Loads the GROBID XML of the paper with the provided DBLP id. If possible uses the XML cache. If not, uses the
      GROBID web service. New results are caches.
      :param paper_id:
      :return an LXML root node of the grobid XML
      """

      filename=cfg.folder_pdf+paper_id+".pdf"
      filename_xml=cfg.folder_content_xml+paper_id+".xml"

      ## check if XML file is already available
      if os.path.isfile(filename_xml):
          ## yes, load from cache
          root=etree.parse(filename_xml)
          # check the validity of the xml
          if self.check_validity_of_xml(root):
              return root
          else:
              raise Exception("Error in xml, pdf  either broken or not extractable (i.e Unicode mapping missing")
      else:
          if not os.path.isfile(filename):
              raise Exception("PDF for "+paper_id+" does not exist.")
          ## no, get from GROBID
          url = cfg.grobid_url + '/processFulltextDocument'
          params = {
              'input': open(filename, 'rb')
          }
          response = requests.post(url, files=params)
          if response.status_code == 200:
              ## it worked. now parse the result to XML
              parser = etree.XMLParser(encoding='UTF-8', recover=True)
              tei = response.content
              tei = tei if not isinstance(tei, text_type) else tei.encode('utf-8')
              root = etree.fromstring(tei, parser)
              ## and store it to xml cache
              with open(filename_xml, 'wb') as f:
                  f.write(etree.tostring(root, pretty_print=True))
              # Check if the xml file derived from a valid pdf with unicode mapping
              # Correct: <teiHeader xml:lang="en">
              # Incorrect: <teiHeader xml:lang="de">
              if self.check_validity_of_xml(root):
                  return root
              else:
                  raise Exception("Error in xml, pdf  either broken or not extractable (i.e Unicode mapping missing)")
          else:
              raise Exception("Error calling GROBID for "+paper_id+": "+str(response.status_code)+" "+response.reason)


  def check_validity_of_xml(self,root):
      string_XML = etree.tostring(root)
      # print(string_XML)
      if "<teiHeader xml:lang=\"en\">" in str(string_XML):
          return True
      else:
          return False

  def process_paper(self, dblpkey, db):
      """
      Loads a paper with the given dblpkey, and extracts its content
      :param dblpkey: the DBLP id of the paper which is to be processed
      :param db: mongo db
      :return:
      """
      NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
      try:
          xml=self.get_grobid_xml(dblpkey)
          result= grobid_mapping.tei_to_dict(xml)
          #
          #try:
          mongo_set_dict=dict()
          #print("results: {}".format(result))
          if 'abstract' in result:
              mongo_set_dict["content.abstract"]=result["abstract"]
          if 'notes' in result:
              mongo_set_dict["content.notes"] = result["notes"]
          if 'fulltext' in result:
              mongo_set_dict["content.fulltext"] = result["fulltext"]
              with open(cfg.folder_content_xml + dblpkey + ".txt", 'w') as f:
                  # f.write(result["fulltext"])
                  print(result["fulltext"])
          if 'chapters' in result:
              mongo_set_dict["content.chapters"] = result["chapters"]

          mongoResult= db.publications.update_one(
              {'_id': dblpkey},
              {'$set': result}
          )
          # print(mongoResult)

          logging.info("Processed "+dblpkey)
      except:
          logging.exception('Cannot process paper ' +dblpkey, exc_info=True)

      # pprint.pprint(result)
      # for ref in result['references']:
      #     print(ref)
      # print(etree.tostring(result['fulltext'], pretty_print=True))


  def process_papers(self, mongo_search_string):
      db = tools.connect_to_mongo()
      # set no_cursor_timeout= true, to avoid "pymongo.errors.CursorNotFound"
      result = db.publications.find(mongo_search_string, no_cursor_timeout=True)
      count = 0
      for r in result:
          self.process_paper(r['dblpkey'], db)
          # sleep after any paper process
          #rnd_time = int(random.uniform(1,3))
          #print("sleep for {} secs!".format(rnd_time))
          #time.sleep(rnd_time)




"""
def main():
    tools.create_all_folders()
    # mongo_search_string = {'_id': 'journals_pvldb_ChaytorW10'}
    # mongo_search_string = {'_id': 'journals_webology_Fedushko14'}
    # mongo_search_string = {'journal': 'PVLDB'}
    # mongo_search_string = {'book': 'SIGIR'}
    # mongo_search_string = {'content': {"$exists": False}}
    # mongo_search_string = ""

    # mongo_search_string = {"dblpkey":"journals_ijclclp_WuC07"}
    #get only the articles
    #mongo_search_string = {"type" : "article"}

    # processable paper
    # mongo_search_string = {'_id': 'journals_mala_Wadler00'}
    # mongo_search_string = {'_id': 'journals_ijclclp_XiaoLW07'}


    # pdf with out unicode mapping
    #mongo_search_string = {'_id': 'journals_iajit_BrahmiaMCB12'}


    # broken pdf
    # mongo_search_string = {'_id': 'journals_sigmod_Snodgrass04'}

    # traverse all the instances in mongo
    #mongo_search_string = {}

    #Specific book title

    for booktitle in booktitles:
        print("Processing booktitle: {}".format(booktitle))
        #{'$and': [{'booktitle': 'ESWC'}, {'content.chapters': {'$exists': True}}]}
        #mongo_search_string = {'content.chapters': {'$exists': False}}
        mongo_search_string = {'$and': [{'booktitle': booktitle}, {'content.chapters': {'$exists': False}}]}
        process_papers(mongo_search_string)

    for journal in journals:
      print("Processing journal: {}".format(journal))
      # {'$and': [{'booktitle': 'ESWC'}, {'content.chapters': {'$exists': True}}]}
      # mongo_search_string = {'content.chapters': {'$exists': False}}
      mongo_search_string = {'$and': [{'journal': journal}, {'content.chapters': {'$exists': False}}]}
      process_papers(mongo_search_string)


    #mongo_search_string = {'content.chapters': {'$exists': False}}
    #process_papers(mongo_search_string)

if __name__ == '__main__':
    main()
"""
