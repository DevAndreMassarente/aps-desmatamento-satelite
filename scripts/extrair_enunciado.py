import re, zlib, sys

data = open(sys.argv[1], 'rb').read()

# ---- parse indirect objects ----
objs = {}
for m in re.finditer(rb'(\d+)\s+(\d+)\s+obj\b', data):
    num = int(m.group(1)); start = m.end()
    end = data.find(b'endobj', start)
    objs[num] = data[start:end if end != -1 else len(data)]

def get_stream(body):
    m = re.search(rb'stream\r?\n', body)
    if not m: return None
    raw = body[m.end():]
    e = raw.rfind(b'endstream')
    if e != -1: raw = raw[:e]
    raw = raw.rstrip(b'\r\n')
    try: return zlib.decompress(raw)
    except Exception:
        try: return zlib.decompressobj().decompress(raw)
        except Exception: return raw

def parse_cmap(txt):
    m = {}
    for blk in re.findall(rb'beginbfchar(.*?)endbfchar', txt, re.S):
        for src, dst in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
            try: m[int(src,16)] = ''.join(chr(int(dst[i:i+4],16)) for i in range(0,len(dst),4))
            except Exception: pass
    for blk in re.findall(rb'beginbfrange(.*?)endbfrange', txt, re.S):
        for lo,hi,dst in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
            a,b,d = int(lo,16), int(hi,16), int(dst,16)
            if b-a > 70000: continue
            for k in range(a,b+1): m[k] = chr(d+(k-a))
    return m

# ---- font resource name -> cmap, per page ----
cmap_cache = {}
def cmap_for_font(fnum):
    if fnum in cmap_cache: return cmap_cache[fnum]
    body = objs.get(fnum, b'')
    tu = re.search(rb'/ToUnicode\s+(\d+)\s+\d+\s+R', body)
    cm = {}
    if tu:
        s = get_stream(objs.get(int(tu.group(1)), b''))
        if s: cm = parse_cmap(s)
    cmap_cache[fnum] = cm
    return cm

# ---- collect pages in order ----
page_objs = [n for n,b in objs.items() if re.search(rb'/Type\s*/Page\b', b) and not re.search(rb'/Type\s*/Pages\b', b)]
page_objs.sort()

def resolve_res(body):
    """return dict fontname -> objnum"""
    r = re.search(rb'/Resources\s+(\d+)\s+\d+\s+R', body)
    res = objs.get(int(r.group(1)), b'') if r else body
    fm = re.search(rb'/Font\s*(\d+)\s+\d+\s+R', res)
    if fm: fdict = objs.get(int(fm.group(1)), b'')
    else:
        fm = re.search(rb'/Font\s*<<(.*?)>>', res, re.S)
        fdict = fm.group(1) if fm else b''
    return {k.decode(): int(v) for k,v in re.findall(rb'/([A-Za-z0-9#_.+-]+)\s+(\d+)\s+\d+\s+R', fdict)}

def content_of(body):
    c = re.search(rb'/Contents\s+(\d+)\s+\d+\s+R', body)
    if c: return get_stream(objs.get(int(c.group(1)), b'')) or b''
    c = re.search(rb'/Contents\s*\[(.*?)\]', body, re.S)
    if c:
        out = b''
        for n in re.findall(rb'(\d+)\s+\d+\s+R', c.group(1)):
            out += (get_stream(objs.get(int(n), b'')) or b'') + b'\n'
        return out
    return b''

def dec_lit(s, cm):
    out = bytearray(); i = 0
    mp = {0x6e:10,0x72:13,0x74:9,0x62:8,0x66:12,0x28:40,0x29:41,0x5c:92}
    while i < len(s):
        c = s[i]
        if c == 0x5c:
            i += 1
            if i >= len(s): break
            n = s[i]
            if n in mp: out.append(mp[n]); i += 1
            elif 0x30 <= n <= 0x37:
                o = ''
                while i < len(s) and 0x30 <= s[i] <= 0x37 and len(o) < 3: o += chr(s[i]); i += 1
                out.append(int(o,8) & 0xFF)
            elif n in (10,13): i += 1
            else: out.append(n); i += 1
        else: out.append(c); i += 1
    if cm: return ''.join(cm.get(x, chr(x)) for x in out)
    return bytes(out).decode('latin-1')

def dec_hex(h, cm):
    h = re.sub(r'\s','',h)
    if len(h) % 2: h += '0'
    b = bytes.fromhex(h)
    if cm:
        return ''.join(cm.get((b[i]<<8)|b[i+1], cm.get(b[i],'')) for i in range(0,len(b)-1,2)) if len(b)>1 else cm.get(b[0],'')
    try: return b.decode('utf-16-be')
    except Exception: return b.decode('latin-1')

TOK = re.compile(rb'/([A-Za-z0-9#_.+-]+)\s+[\d.]+\s+Tf|\[(.*?)\]\s*TJ|\((.*?)(?<!\\)\)\s*Tj|<([0-9A-Fa-f\s]+)>\s*Tj|(T\*|\bTd\b|\bTD\b|\bET\b)', re.S)

for pi, pnum in enumerate(page_objs, 1):
    body = objs[pnum]
    fonts = resolve_res(body)
    cs = content_of(body)
    cm = {}
    out = []
    for m in TOK.finditer(cs):
        if m.group(1):
            cm = cmap_for_font(fonts.get(m.group(1).decode(), -1))
        elif m.group(2) is not None:
            buf = []
            for mm in re.finditer(rb'\((.*?)(?<!\\)\)|<([0-9A-Fa-f\s]+)>|(-?[\d.]+)', m.group(2), re.S):
                if mm.group(1) is not None: buf.append(dec_lit(mm.group(1), cm))
                elif mm.group(2) is not None: buf.append(dec_hex(mm.group(2).decode(), cm))
                elif mm.group(3) and float(mm.group(3)) < -120: buf.append(' ')
            out.append(''.join(buf))
        elif m.group(3) is not None: out.append(dec_lit(m.group(3), cm))
        elif m.group(4) is not None: out.append(dec_hex(m.group(4).decode(), cm))
        else: out.append('\n')
    t = ''.join(out)
    t = re.sub(r'[ \t]+\n', '\n', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    print(f'\n{"="*72}\n===== PAGINA {pi} (obj {pnum}) =====\n{"="*72}')
    print(t.strip())
