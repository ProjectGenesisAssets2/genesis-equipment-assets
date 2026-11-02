#!/usr/bin/env python3
"""Download Git blob fragments from the public Genesis Equipment repo and
rehydrate the exact V03 GLB in a temporary GitHub Actions workspace.

Objects were uploaded to GitHub's Git blob store via the authorized
GitHub connection but are not stored as normal repository files.
Verifies every raw Git blob object SHA1 and final SHA256.
"""
import base64
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

def download_blob(owner_repo, sha, token, attempts=4):
    url=f"https://api.github.com/repos/{owner_repo}/git/blobs/{sha}"
    headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28",
             "User-Agent":"Genesis-V03-Cycles-Binary-Handoff"}
    if token: headers["Authorization"]=f"Bearer {token}"
    for k in range(attempts):
        try:
            req=urllib.request.Request(url,headers=headers)
            with urllib.request.urlopen(req,timeout=40) as resp:
                doc=json.load(resp)
            if doc.get("encoding")!="base64" or doc.get("sha")!=sha:
                raise RuntimeError(f"Unexpected git blob response for {sha}")
            chunk=base64.b64decode(doc["content"],validate=False)
            git_sha=hashlib.sha1(f"blob {len(chunk)}\0".encode()+chunk).hexdigest()
            if git_sha!=sha: raise ValueError(f"Git blob hash mismatch: {sha} != {git_sha}")
            return chunk
        except (urllib.error.URLError, TimeoutError) as exc:
            if k==attempts-1: raise
            print(f"[GENESIS] retry blob {sha[:8]} after {exc}",flush=True)
            time.sleep(3*(k+1))

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    m=json.loads(a.manifest.read_text(encoding="utf8"))
    if m["kind"]!="GitBlobChunksV1" or len(m["blobs"])!=21:
        raise ValueError("Unexpected manifest")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256()
    total=0
    with a.output.open("wb") as f:
        for i,sha in enumerate(m["blobs"]):
            data=download_blob(os.environ["GITHUB_REPOSITORY"],sha,os.environ.get("GITHUB_TOKEN",""))
            expected=min(m["chunk_bytes"],m["size_bytes"]-i*m["chunk_bytes"])
            if len(data)!=expected:
                raise ValueError(f"Chunk {i} length mismatch: {len(data)} != {expected}")
            f.write(data);digest.update(data);total+=len(data)
            print(f"[GENESIS] {i+1}/{len(m['blobs'])} chunks ({total:,} bytes)",flush=True)
    if digest.hexdigest()!=m["sha256"] or total!=m["size_bytes"]:
        a.output.unlink(missing_ok=True)
        raise ValueError("Final source hash or size mismatch")
    print(f"GENESIS_V03_VERIFIED {total} {digest.hexdigest()}",flush=True)

if __name__=="__main__":main()
