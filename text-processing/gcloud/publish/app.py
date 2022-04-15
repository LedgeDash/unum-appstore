import json
import uuid
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from google.cloud import firestore
from google.cloud import exceptions as gcloudexceptions

with open("dbconfig.yaml") as f:
    config = yaml.load(f.read(), Loader=Loader)
    db_name = config["PostDatabase"]

post_db = firestore.Client()

COLLECTION_NAME='text-processing-posts'

def lambda_handler(event, context):

    user_names=event['user_names']
    urls = event['urls']
    
    document_name = f'{uuid.uuid4()}'
    doc_ref = post_db.collection(u'{}'.format(COLLECTION_NAME)).document(u'{}'.format(document_name))
    value = {'postid': document_name, 'user_names': user_names, 'urls': urls}
    
    try:
        doc_ref.create(value)
    except gcloudexceptions.Conflict as e:
        print(f'Document {document_name} already exists: {e}')
        return -1
    except Exception as e:
        raise e

    return event
