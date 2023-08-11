import uvicorn

from userdata_api.routes.base import app

import argparse
from worker.consumer import process

def get_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    start = subparsers.add_parser("start")
    start.add_argument('--instance', type=str, required=True)

    return parser.parse_args()



if __name__ == '__main__':
    args = get_args()
    match args.instance:
        case "api":
            uvicorn.run(app)
        case "worker":
            process()

