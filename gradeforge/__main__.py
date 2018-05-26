from argparse import ArgumentParser
from gradeforge.src.utils import SingleMetavarFormatter

parser = ArgumentParser(formatter_class=SingleMetavarFormatter)
subparsers = parser.add_subparsers(help='commands to run')

web = subparsers.add_parser('web', description='run the web server')
web.add_argument('--port', '-p', type=int, default=5000)

post = subparsers.add_parser('post', description='download files from sc.edu')


parse = subparsers.add_parser('parse', description='parse downloaded files')

args = parser.parse_args()

