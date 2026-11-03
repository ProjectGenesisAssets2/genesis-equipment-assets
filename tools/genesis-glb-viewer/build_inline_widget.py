from pathlib import Path
import json
root=Path(__file__).resolve().parent
tpl=(root/'inline-widget-template.html').read_text()
payload=(root/'sword-payload-gzip.b64').read_text().strip()
nodes=json.loads((root/'sword-payload-meta.json').read_text())['instances']
html=tpl.replace('__PAYLOAD__',payload).replace('__INSTANCES__',json.dumps(nodes,separators=(',',':')))
(root/'inline-selfcontained.html').write_text(html,encoding='utf8')
print('SELFCONTAINED_HTML_BYTES',len(html.encode()))
