import logging
from pyhelpers import tools, grobid_mapping
import config
tools.setup_logging()
import pprint
import json


def main(filter:("filter","option")=None):
    """

    :param filter: -filter="{'printConf' : 'yes', 'printJournal' : 'yes', 'printColl': 'yes', 'showPdfProg' :'yes', 'showExtractedSents':'yes'}"
    :return:
    """


    filters = json.loads(filter.replace("'", '"'))
    if filter:
        filters = json.loads(filter.replace("'", '"'))
        print("Using filters " + str(filters))
    print(filters)
    db = tools.connect_to_mongo()
    if len(filters) > 0:
        for k, v in filters.items():
            if k == "showPdfProg" and v == "yes":

                result = db.downloads.count({"success" : True})
                print('{:>25} {:>8d}'.format("PDFs downloaded", result))
                #
                result = db.downloads.count({"success": False})
                print('{:>25} {:>8d}'.format("broken DBLP links", result))
                #
                result = db.publications.count({"content": {"$exists": True}})
                print('{:>25} {:>8d}'.format("fulltexts extracted", result))

                #print the papers from WWW
                result = db.publications.count({"booktitle": "WWW"})
                print('{:>25} {:>8d}'.format("WWW papers", result))

                result = db.publications.count({'$and' : [{'booktitle' :'WWW'} , {'content.chapters':{'$exists':True}}]})
                print('{:>25} {:>8d}'.format("Successful extractions WWW papers", result))

                #print the papers from SIGIR
                result = db.publications.count({"booktitle": "SIGIR"})
                print('{:>25} {:>8d}'.format("SIGIR papers", result))

                result = db.publications.count({'$and' : [{'booktitle' :'SIGIR'} , {'content.chapters':{'$exists':True}}]})
                print('{:>25} {:>8d}'.format("Successful extractions SIGIR papers", result))


                #print the papers from ESWC
                result = db.publications.count({"booktitle": "ESWC"})
                print('{:>25} {:>8d}'.format("ESWC papers", result))

                #result = db.publications.find_one({"dblpkey":"conf_esws_BruggemannBXK16"})
                #print(result)
                #if result is None:
                #    print("No entry")


                result = db.publications.count({'$and' : [{'booktitle' :'ESWC'} , {'content.chapters':{'$exists':True}}]})
                print('{:>25} {:>8d}'.format("Successful extractions ESWC papers", result))

                #print the papers from ICWSM
                result = db.publications.count({"booktitle": "ICWSM"})
                print('{:>25} {:>8d}'.format("ICWSM papers", result))

                result = db.publications.count({'$and' : [{'booktitle' :'ICWSM'} , {'content.chapters':{'$exists':True}}]})
                print('{:>25} {:>8d}'.format("Successful extractions ICWSM papers", result))


                #print the papers from VLDB
                result = db.publications.count({"booktitle": "VLDB"})
                print('{:>25} {:>8d}'.format("VLDB papers", result))

                result = db.publications.count({'$and' : [{'booktitle' :'VLDB'} , {'content.chapters':{'$exists':True}}]})
                print('{:>25} {:>8d}'.format("Successful extractions VLDB papers", result))

            if k == "printColl" and v == "yes":
                print("Collections in MongoDB")
                collections = db.collection_names()
                for collection in collections:
                    print(collection)
                print()

            if k == "showExtractedSents" and v == "yes":
                sentences = db.sentences.find({}).count()
                print("Extracted Sentences: {}".format(sentences))

                sentences = db.sentences.find({"objective": 1}).count()
                print("Extracted Sentences objective: {}".format(sentences))

                sentences = db.sentences.find({"method": 1}).count()
                print("Extracted Sentences method: {}".format(sentences))

                sentences = db.sentences.find({"software": 1}).count()
                print("Extracted Sentences software: {}".format(sentences))

                sentences = db.sentences.find({"dataset": 1}).count()
                print("Extracted Sentences dataset: {}".format(sentences))

                sentences = db.sentences.find({"result": 1}).count()
                print("Extracted Sentences result: {}".format(sentences))

                sentences = db.sentences.find({"other": 1}).count()
                print("Extracted Sentences other: {}".format(sentences))


                print()
            if k == "printConf" and v == "yes":
                result = db.publications.distinct("booktitle")
                # print("Booktitles")
                f = open(config.folder_log + "booktitles_summary.csv", "w", encoding="UTF-8")
                for r in result:
                    count_booktitle = db.publications.find({"booktitle": r}).count()
                    f.write("{},{}".format(r, count_booktitle))
                    f.write("\n")
                    # print("{}: {}".format(r, count_booktitle))
                f.close()

            if k == "printJournal" and v == "yes":
                result = db.publications.distinct("journal")
                # print("Journals")
                f = open(config.folder_log + "journal_summary.csv", "w", encoding="UTF-8")
                for r in result:
                    count_journal = db.publications.find({"journal": r}).count()
                    f.write("{},{}".format(r, count_journal))
                    f.write("\n")
                    # print("{}: {}".format(r,count_journal))
                f.close()
    else:
        print("Use filters e.g.  -filter=\"{'printConf' : 'yes', 'printJournal' : 'yes', 'printColl': 'yes', 'showPdfProg' :'yes', 'showExtractedSents}")
    """
    result = db.publications.distinct("journal")
    #print("Journals")
    f = open(config.folder_log+"journal_summary.csv", "w", encoding="UTF-8")
    for r in result:
        count_journal = db.publications.find({"journal": r}).count()
        f.write("{},{}".format(r,count_journal))
        f.write("\n")
        #print("{}: {}".format(r,count_journal))
    f.close()


    result = db.publications.distinct("booktitle")
    #print("Booktitles")
    f = open(config.folder_log+"booktitles_summary.csv", "w", encoding="UTF-8")
    for r in result:
        count_booktitle = db.publications.find({"booktitle": r}).count()
        f.write("{},{}".format(r, count_booktitle))
        f.write("\n")
        #print("{}: {}".format(r, count_booktitle))
    f.close()
    """

if __name__ == '__main__':
    import plac
    plac.call(main)
