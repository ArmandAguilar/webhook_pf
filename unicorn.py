import sys
import uvicorn
import logging
from uvicorn.config import LOGGING_CONFIG

if __name__ == "__main__":

    uvicorn.run('main:app', host='0.0.0.0', port=8090, workers=10)