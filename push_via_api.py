# -*- coding: utf-8 -*-
"""GitHub API 推送脚本（当 git push 被网络/代理阻断时的可靠通道）
用法: python push_via_api.py [仓库目录] [分支] [commit信息]
说明: 读取 ~/.git-credentials 中的 PAT，通过 Git Data API (blobs/trees/commits/refs) 推送，
      api.github.com 通常比 github.com 直连稳定。
"""
import base64, json, os, re, subprocess, sys, urllib.request

REPO_DIR = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
BRANCH = sys.argv[2] if len(sys.argv) > 2 else "main"
MESSAGE = sys.argv[3] if len(sys.argv) > 3 else "update"

def token():
    p = os.path.expanduser("~/.git-credentials")
    m = re.search(r"https://[^:]*:([^@]*)@github\.com", open(p, encoding="utf-8").read())
    if not m:
        raise SystemExit("未找到 GitHub PAT (~/.git-credentials)")
    return m.group(1)

def repo_slug(d):
    url = subprocess.check_output(["git", "-C", d, "remote", "get-url", "origin"]).decode().strip()
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", url)
    if not m:
        raise SystemExit("无法解析 origin 仓库地址: " + url)
    return m.group(1), m.group(2)

TOKEN = token()
OWNER, REPO = repo_slug(REPO_DIR)
API = f"https://api.github.com/repos/{OWNER}/{REPO}"

def call(url, method="GET", data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", "token " + TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "wb-deploy")
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, body, timeout=90) as r:
        return json.loads(r.read().decode())

def git_paths(*args):
    """git 输出用 -z 取 NUL 分隔，避免中文路径被转义/加引号"""
    out = subprocess.check_output(["git", "-C", REPO_DIR, *args])
    return [s.decode("utf-8") for s in out.split(b"\0") if s]


def main():
    # 待推送文件 = 最近一次提交改动的文件（回退：全部跟踪文件）
    files = git_paths("ls-files", "-z")
    changed = git_paths("diff", "--name-only", "-z", "HEAD~1", "HEAD")
    targets = changed or files
    ref = call(f"{API}/git/ref/heads/{BRANCH}")
    base_sha = ref["object"]["sha"]
    base = call(f"{API}/git/commits/{base_sha}")
    tree = []
    for fn in targets:
        path = os.path.join(REPO_DIR, fn)
        if not os.path.isfile(path):
            continue
        blob = call(f"{API}/git/blobs", "POST", {
            "content": base64.b64encode(open(path, "rb").read()).decode(), "encoding": "base64"})
        tree.append({"path": fn, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print("blob", fn, blob["sha"][:8])
    new_tree = call(f"{API}/git/trees", "POST", {"base_tree": base["tree"]["sha"], "tree": tree})
    commit = call(f"{API}/git/commits", "POST", {
        "message": MESSAGE, "tree": new_tree["sha"], "parents": [base_sha]})
    call(f"{API}/git/refs/heads/{BRANCH}", "PATCH", {"sha": commit["sha"], "force": True})
    print("OK 已推送", OWNER + "/" + REPO, "commit", commit["sha"][:8])

if __name__ == "__main__":
    main()
