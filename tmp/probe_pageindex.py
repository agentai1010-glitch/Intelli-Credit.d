from pageindex import PageIndexClient
import inspect, os
from dotenv import load_dotenv
load_dotenv('.env')
c = PageIndexClient(api_key=os.getenv('PAGEINDEX_API_KEY'))
print("submit_document signature:", inspect.signature(c.submit_document))
print("submit_query signature:", inspect.signature(c.submit_query))
