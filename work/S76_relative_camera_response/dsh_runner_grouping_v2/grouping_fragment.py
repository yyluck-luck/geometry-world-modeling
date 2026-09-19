WORKSPACE_ID = 'a638e86f-4d3a-42bb-ad92-2dbe0383161d'
LOCAL_ORIGIN = 'http://127.0.0.1:3080'


def session_paths():
    """Directory inventory only, no old session contents."""
    return {str(p) for p in (DSH_HOME / 'sessions').glob('*/session-*/session.jsonl.zstd') if p.is_file()}


def new_session_header(path):
    """Read exactly the first Zstandard frame, which official storage reserves for the header."""
    p = Path(path)
    if not p.resolve().is_relative_to((DSH_HOME / 'sessions').resolve()):
        raise ValueError('Session path escaped expected storage')
    chunks = []; consumed = 0
    with p.open('rb') as handle:
        def take(n):
            nonlocal consumed
            if n < 0 or consumed + n > 1024 * 1024:
                raise ValueError('Header frame exceeds bounded metadata budget')
            b = handle.read(n)
            if len(b) != n:
                raise ValueError('Incomplete header frame')
            consumed += n; chunks.append(b)
            return b
        if take(4) != bytes.fromhex('28b52ffd'):
            raise ValueError('Unexpected Zstandard frame magic')
        descriptor = take(1)[0]
        if descriptor & 24:
            raise ValueError('Reserved Zstandard header bits')
        single = bool(descriptor & 32); flag = descriptor >> 6; dictionary = descriptor & 3
        take((0 if single else 1) + (4 if dictionary == 3 else dictionary)
             + ((1 if single else 0) if flag == 0 else 1 << flag))
        while True:
            block = int.from_bytes(take(3), 'little'); kind = (block >> 1) & 3
            if kind == 3:
                raise ValueError('Reserved Zstandard block type')
            take(1 if kind == 1 else block >> 3)
            if block & 1:
                break
        if descriptor & 4:
            take(4)
    # Only a single header line is decoded; no remaining compressed bytes are read.
    code = """const fs=require('node:fs');const z=require('node:zlib');
const b=z.zstdDecompressSync(fs.readFileSync(0),{maxOutputLength:1048576});
if(!b.length||b.indexOf(10)!==b.length-1)throw Error('not one header line');
const h=JSON.parse(b.toString('utf8'));
if(h.type!=='session'||typeof h.id!=='string'||typeof h.cwd!=='string')throw Error('bad header');
process.stdout.write(JSON.stringify({id:h.id,cwd:h.cwd}));"""
    reply = subprocess.run([str(NODE), '-e', code], input=b''.join(chunks),
                           capture_output=True, timeout=5, check=True)
    header = json.loads(reply.stdout)
    if not re.fullmatch(r'session-[A-Za-z0-9_-]+', header['id']):
        raise ValueError('Expected full session- identifier')
    return dict(path=str(p), id=header['id'], cwd=header['cwd'], header_compressed_bytes=consumed)


def attach_new_session(before, output):
    """Best-effort local UI grouping. Never changes a historical session cwd."""
    import http.cookiejar
    import urllib.parse
    import urllib.request
    import uuid
    result = dict(status='NOT_COMPLETED', workspace_id=WORKSPACE_ID, observed_utc=utc(),
                  model_return_independent=True, new_candidates=[], header_read_errors=[])
    try:
        fresh = sorted(session_paths() - before)
        result['new_file_count'] = len(fresh)
        matches = []
        for path in fresh:
            try:
                header = new_session_header(path)
                result['new_candidates'].append(header)
                if header['cwd'] == str(ROOT):
                    matches.append(header)
            except Exception as error:
                result['header_read_errors'].append(dict(path=path, error_type=type(error).__name__))
        # A failed new-header read can hide a second matching session: fail closed.
        if result['header_read_errors'] or len(matches) != 1:
            result['reason'] = 'NO_UNIQUE_COMPLETE_NEW_PROJECT_HEADER'
            return result
        selected = matches[0]; result['session_id'] = selected['id']
        def check_local(url):
            parsed = urllib.parse.urlsplit(url)
            if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.port != 3080
                    or parsed.username is not None or parsed.password is not None):
                raise ValueError('Only exact loopback origin is allowed')
            return url
        class LocalRequests(urllib.request.BaseHandler):
            def http_request(self, request):
                check_local(request.full_url); return request
            https_request = http_request
        class LocalRedirects(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, request, fp, code, msg, headers, newurl):
                check_local(newurl)
                return super().redirect_request(request, fp, code, msg, headers, newurl)
        # Bootstrap secret is consumed in memory only, never copied to output or an exception message.
        private_log = DSH_HOME / 'web_startup_private.log'
        text = private_log.read_text()
        urls = re.findall(r'http://127\.0\.0\.1:3080/[^\s\x1b<>"\']+', text)
        bootstraps = [u for u in urls if urllib.parse.urlsplit(u).query]
        if not bootstraps:
            raise ValueError('No loopback bootstrap URL in known private startup log')
        bootstrap = check_local(bootstraps[-1])
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), LocalRequests(),
                    LocalRedirects(), urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        with opener.open(bootstrap, timeout=5) as response:
            check_local(response.geturl())
        wire = dict(type='client-request', rpcId=str(uuid.uuid4()), method='session/create',
                    payload=dict(args=dict(request=dict(workspaceId=WORKSPACE_ID, sessionId=selected['id']))))
        request = urllib.request.Request(LOCAL_ORIGIN + '/api/session/create',
            data=json.dumps(wire).encode(), method='POST',
            headers={'Content-Type': 'application/json', 'Origin': LOCAL_ORIGIN})
        with opener.open(request, timeout=5) as response:
            check_local(response.geturl()); payload = response.read(65537)
        if len(payload) > 65536:
            raise ValueError('Unexpected oversized local RPC response')
        reply = json.loads(payload); api = reply.get('result', {})
        if api.get('ok') is True and api.get('value', {}).get('sessionId') == selected['id']:
            result.update(status='ATTACHED_PROJECT_WORKSPACE', api_ok=True)
        else:
            result.update(reason='LOCAL_API_DID_NOT_CONFIRM_EXACT_SESSION', api_ok=api.get('ok'))
    except Exception as error:
        result.update(status='NOT_COMPLETED', reason='LOCAL_GROUPING_ERROR', error_type=type(error).__name__)
    finally:
        result['completed_utc'] = utc()
        write_json(output / 'GROUPING.json', result)
    return result


