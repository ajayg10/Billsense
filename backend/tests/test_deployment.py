"""Offline verification of generated routing and deployment command safety."""
import importlib.util
from pathlib import Path
import json
import os
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('amplify_rewrites',ROOT/'infra/amplify-rewrites.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def test_rules_preserve_api_prefix_and_order():
    rules=module.rules('https://example.execute-api.us-east-1.amazonaws.com/')
    assert rules[0]['source']=='/api/<*>'
    assert rules[0]['target']=='https://example.execute-api.us-east-1.amazonaws.com/api/<*>'
    assert rules[1]['source']=='/api'
    assert rules[-1]['target']=='/index.html'
    assert all(r['status']=='200' for r in rules)
    assert json.loads(json.dumps(rules))==rules

@pytest.mark.parametrize('origin',['http://example.com','https://example.com/api','https://example.com/prod','https://user:pass@example.com','https://example.com?x=1','https://example.com#x','https://example.com:443',''])
def test_reject_ambiguous_proxy_origins(origin):
    with pytest.raises(ValueError):module.rules(origin)

def test_deploy_script_never_runs_frontend_publish_and_uses_built_template(tmp_path):
    """Run the actual shell script against AWS/SAM stubs, without cloud calls."""
    import shutil
    project=tmp_path/'project';(project/'infra').mkdir(parents=True)
    for name in ['deploy.sh','amplify-rewrites.py']:
        shutil.copy(ROOT/'infra'/name,project/'infra'/name)
    bins=tmp_path/'bin';bins.mkdir()
    logfile=tmp_path/'calls'
    aws='''#!/usr/bin/env python3
import sys,os,json
with open(os.environ['CALLS'],'a') as f:f.write(json.dumps(['aws']+sys.argv[1:])+'\\n')
if sys.argv[1:3]==['cloudformation','list-stacks']:print('[]')
elif sys.argv[1:3]==['cloudformation','describe-stacks']:print('https://example.execute-api.us-east-1.amazonaws.com')
else:print('ok')
'''
    sam='''#!/usr/bin/env python3
import sys,os,json
with open(os.environ['CALLS'],'a') as f:f.write(json.dumps(['sam']+sys.argv[1:])+'\\n')
'''
    for name,body in [('aws',aws),('sam',sam)]:
        p=bins/name;p.write_text(body);p.chmod(0o755)
    env=os.environ | {'PATH':str(bins)+':'+os.environ['PATH'],'CALLS':str(logfile),'SAM_USE_CONTAINER':'false','AI_ENABLED':'false','BILLSENSE_STACK':'billsense-backend','AWS_REGION':'us-east-1'}
    result=subprocess.run(['bash',str(project/'infra/deploy.sh')],env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    calls=[json.loads(line) for line in logfile.read_text().splitlines()]
    deploy=next(c for c in calls if c[:2]==['sam','deploy'])
    assert deploy[deploy.index('--template-file')+1]=='.aws-sam/backend/template.yaml'
    assert deploy[deploy.index('--stack-name')+1]=='billsense-backend'
    assert not any(c[:2] in (['aws','s3'],['aws','cloudfront']) for c in calls)
    generated=json.loads((project/'infra/amplify-rewrites.generated.json').read_text())
    assert generated[0]['target'].endswith('/api/<*>')

def test_deploy_refuses_existing_full_stack(tmp_path):
    bins=tmp_path/'bin';bins.mkdir()
    (bins/'aws').write_text('''#!/usr/bin/env python3
import sys
if sys.argv[1:3]==['cloudformation','list-stacks']:print('["billsense-backend"]')
elif sys.argv[1:3]==['cloudformation','list-stack-resources']:print('["AWS::S3::Bucket","AWS::CloudFront::Distribution"]')
else:print('ok')
''')
    (bins/'sam').write_text('#!/bin/sh\necho SHOULD_NOT_RUN\nexit 99\n')
    for p in bins.iterdir():p.chmod(0o755)
    env=os.environ|{'PATH':str(bins)+':'+os.environ['PATH'],'AI_ENABLED':'false','BILLSENSE_STACK':'billsense-backend'}
    result=subprocess.run(['bash',str(ROOT/'infra/deploy.sh')],env=env,capture_output=True,text=True)
    assert result.returncode==1
    assert 'Choose a new BILLSENSE_STACK name' in result.stderr
    assert 'SHOULD_NOT_RUN' not in result.stdout
