import os
os.chdir('backend')
from dotenv import load_dotenv
load_dotenv()
print('KEY:', repr(os.getenv('STEPFUN_API_KEY')))
print('URL:', repr(os.getenv('STEPFUN_BASE_URL')))