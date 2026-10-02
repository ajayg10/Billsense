#!/usr/bin/env python3
"""Print Amplify rewrite JSON from a deployed HTTP API origin; no AWS calls."""
import argparse
import json
import sys
from urllib.parse import urlsplit

# AWS's documented SPA rule. API rules MUST precede this fallback.
SPA_SOURCE = r'</^[^.]+$|\.(?!(css|gif|ico|jpg|js|png|txt|svg|woff|woff2|ttf|map|json|webp)$)([^.]+$)/>'

def rules(api_url):
    url = urlsplit(api_url.strip())
    if (url.scheme != 'https' or not url.hostname or url.username or url.password
            or url.path not in ('', '/') or url.query or url.fragment or url.port):
        raise ValueError('Use the HTTPS API origin only, with no /api, stage, port, query, or credentials.')
    origin = f'https://{url.netloc}'
    return [
        {'source':'/api/<*>','target':origin+'/api/<*>','status':'200','condition':None},
        {'source':'/api','target':origin+'/api','status':'200','condition':None},
        {'source':SPA_SOURCE,'target':'/index.html','status':'200','condition':None},
    ]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('api_url', help='ApiUrl output from the billsense-backend SAM stack')
    args=parser.parse_args()
    try:
        print(json.dumps(rules(args.api_url), indent=2))
    except ValueError as error:
        parser.error(str(error))

if __name__=='__main__':
    main()
