#!/usr/bin/env python3
"""Build easyopenhub.com as plain static HTML (no browser, no npm) into the repo root.

Inputs (never modified here):
  data/github_apps.json   open-source apps (hand-edited: repo, alternative_to, pitch, group, video ...)
  data/manual_apps.json   mark's own / featured apps (hand-edited only)
  data/releases.json      written by scripts/sync_releases.py (version, date, .dmg links)
Outputs: index.html, 404.html, en/, zh/, sitemap.xml, robots.txt, llms.txt, CNAME, .nojekyll
Status: priority = featured Mac picks (ranked), keep = live but not featured, retired = page kept (noindex) so old links work.
"""
import json, os, re, html, shutil, datetime, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, *p)
DOMAIN = "easyopenhub.com"; BASE = f"https://{DOMAIN}"
APPS = json.load(open(D("data", "github_apps.json")))
MANUAL = json.load(open(D("data", "manual_apps.json")))
REL = json.load(open(D("data", "releases.json"))) if os.path.exists(D("data", "releases.json")) else {}
GUIDE = {L: open(D("scripts", "content", f"guide_{L}.html")).read() for L in ("en", "zh")}
TODAY = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=5)).date().isoformat()  # New York
E = lambda s: html.escape(str(s or ""), quote=True)
LIVE = [a for a in APPS if a["status"] != "retired"]
PRI = sorted([a for a in APPS if a["status"] == "priority"], key=lambda a: a["rank"] or 999)
KEEP = sorted([a for a in APPS if a["status"] == "keep"], key=lambda a: -(a.get("stars") or 0))
NORM = {"Photoshop Generative Fill": "Adobe Photoshop", "Claude": "Claude Pro", "ChatGPT": "ChatGPT Plus", "Adobe Premiere Pro": "Premiere Pro", "ILovePDF": "iLovePDF",
        "Dragon NaturallySpeaking": "Dragon"}
# paid apps US Mac users search alternatives for: they get a page even with a single pick
FOCUS = {"CapCut", "Adobe Photoshop", "Adobe Illustrator", "Adobe Lightroom", "Adobe Audition", "Microsoft 365", "Excel", "MacWhisper Pro", "CleanMyMac", "Bartender", "Raycast Pro", "Screen Studio", "Permute", "Notion", "CleanShot X", "1Password",
         "Wispr Flow", "Superwhisper", "Topaz Gigapixel AI", "Paste", "Loom", "TeamViewer", "Final Cut Pro", "Evernote",
         "Midjourney", "ElevenLabs", "Otter.ai", "Adobe Acrobat", "Snagit", "Camtasia", "Granola", "Descript", "Dropbox"}
alts = lambda a: list(dict.fromkeys(NORM.get(x, x) for x in (a.get("alternative_to") or [])))
is_mac = lambda a: "macOS" in (a.get("platforms") or [])
aslug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
T = {
 "en": dict(lang="en-US", home="/", nav=[("Mac Apps", "/"), ("Alternatives", "/en/alternatives/"), ("Guide", "/en/guide/"), ("About", "/en/about/")],
   other="中文", replaces="Replaces", get="Get it from the official site", gh="View on GitHub Releases", src="Source on GitHub",
   ver="Version", upd="updated", which="Which Mac do I have?",
   which_a="Apple menu  → About This Mac. If it says <b>Chip: Apple M1, M2, M3 or M4</b>, use Apple Silicon. If it says <b>Processor: Intel</b>, use Intel. Not sure? Universal works on both.",
   blocked="Mac says it can’t be opened?",
   blocked_a="Many open-source apps aren’t paid-signed by Apple, so the first launch shows a warning. If you downloaded it from the button above (the developer’s own release), open <b>System Settings → Privacy &amp; Security</b>, scroll down and click <b>Open Anyway</b>. <a href=\"/en/guide/\">Full safety checklist</a>.",
   notmac="Not available for Mac. Platforms:", watch="Watch the 45-second demo", what="What it does", good="Good for", skip="Skip it if",
   steps="How to start", note="Heads-up", faq="Questions", more_alt="More {a} alternatives", featured="Indie Pick",
   all="All", search="Search apps or the paid app you want to replace…", morehdr="More open-source apps", morep="Windows, iPhone, web apps and games. Not the focus of this site, but still handy.",
   replhdr="Replace a paid app", trust="Every download links to the developer’s own official release. We don’t host, modify or bundle anything. No ad networks.",
   built="Curated by an indie developer who got tired of hunting for .dmg files on GitHub."),
 "zh": dict(lang="zh-CN", home="/zh/", nav=[("精选 Mac 软件", "/zh/"), ("付费软件平替", "/zh/alternatives/"), ("新手指南", "/zh/guide/"), ("关于", "/zh/about/")],
   other="English", replaces="可替代", get="去官网下载", gh="到 GitHub Releases 查看", src="GitHub 原址",
   ver="版本", upd="更新于", which="我的 Mac 是哪种芯片？",
   which_a="点左上角苹果图标 → 关于本机。写着 <b>芯片 Apple M1/M2/M3/M4</b> 就选 M 芯片版；写着 <b>处理器 Intel</b> 就选 Intel 版。不确定就下通用版。",
   blocked="Mac 提示“无法打开”？",
   blocked_a="很多开源软件没有付费签名，第一次打开会被系统拦。确认是从上面按钮（作者官方发布）下载的，就打开 <b>系统设置 → 隐私与安全性</b>，往下拉点 <b>仍要打开</b>。<a href=\"/zh/guide/\">完整安全清单</a>。",
   notmac="暂无 Mac 版。支持：", watch="看 45 秒演示", what="能干嘛", good="适合谁", skip="不适合", steps="怎么开始", note="提醒", faq="常见问题",
   more_alt="更多 {a} 平替", featured="作者自研", all="全部", search="搜软件名，或者你想替代的付费软件…",
   morehdr="更多开源软件", morep="Windows、手机、网页版和游戏。不是本站重点，但也好用。", replhdr="替代付费软件",
   trust="所有下载都直连原作者的官方发布，本站不托管、不修改、不捆绑，也不接广告联盟。", built="一个受够了在 GitHub 上找 .dmg 的独立开发者整理。"),
}
DLZ = {"universal": "下载 Mac 通用版（所有芯片）", "apple_silicon": "下载 Mac 版（M1–M4 芯片）", "intel": "下载 Mac 版（老款 Intel 芯片）"}
GROUPS = ["Screen & Video", "Photo & Design", "Productivity", "Voice & Audio", "AI", "Utilities"]
GZ = {"Productivity": "效率办公", "Screen & Video": "视频与录屏", "Photo & Design": "修图与设计", "Voice & Audio": "语音与音频", "AI": "AI", "Utilities": "实用工具"}
LOGO = open(D("logo.svg")).read() if os.path.exists(D("logo.svg")) else ""
LOGO = re.sub(r"<\?xml.*?\?>", "", LOGO)

def ld_tag(objs):
    return "".join('<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False).replace("</", "<\\/") + "</script>" for o in objs)

def page(L, title, desc, path, body, other_path=None, noindex=False, ld=(), og_img=None):
    t = T[L]; op = other_path
    alt = ""
    if op:
        en_p, zh_p = (path, op) if L == "en" else (op, path)
        alt = (f'<link rel="alternate" hreflang="en-US" href="{BASE}{en_p}"><link rel="alternate" hreflang="zh-CN" href="{BASE}{zh_p}">'
               f'<link rel="alternate" hreflang="x-default" href="{BASE}{en_p}">')
    nav = "".join(f'<a href="{h}">{E(n)}</a>' for n, h in t["nav"])
    sw = f'<a class="lang" href="{op or ("/zh/" if L == "en" else "/")}" hreflang="{"zh-CN" if L == "en" else "en-US"}">{t["other"]}</a>'
    return f"""<!doctype html>
<html lang="{t['lang']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{BASE}{path}">{alt}
{'<meta name="robots" content="noindex,follow">' if noindex else ''}
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{BASE}{path}"><meta property="og:type" content="website">{f'<meta property="og:image" content="{BASE}/{og_img}">' if og_img else ''}
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)"><meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css">
<script>try{{var m=localStorage.getItem('theme');if(m)document.documentElement.dataset.theme=m}}catch(e){{}}</script>{ld_tag(ld)}
</head><body>
<header class="top"><div class="wrap bar"><a class="brand" href="{t['home']}">{LOGO}<span><b>Easy</b>OpenHub</span></a>
<nav>{nav}{sw}<button class="theme" type="button" aria-label="Switch light or dark mode">◐</button></nav></div></header>
<main class="wrap">{body}</main>
<footer class="wrap foot"><p><b>{E(t['trust'])}</b></p><p>{E(t['built'])} <a href="/{L}/about/">{'About &amp; Security' if L == 'en' else '关于与安全'}</a> · <a href="/{L}/guide/">{t['nav'][2][0]}</a> · <a href="/{L}/alternatives/">{t['nav'][1][0]}</a></p>
<p class="muted">© 2026 EasyOpenHub. {'App names and trademarks belong to their owners. Open-source apps are made by their own developers.' if L == 'en' else '软件名称和商标归各自所有者。开源软件由各自作者开发。'}</p></footer>
<script src="/assets/site.js" defer></script></body></html>
"""

def rel_of(a): return REL.get(a.get("repo") or "") or {}

def dl_buttons(a, L, compact=False):
    t = T[L]; r = rel_of(a); ds = r.get("downloads") or []
    if is_mac(a) and ds:
        btns = "".join(f'<a class="btn {"pri" if n == 0 else "sec"}" href="{E(d["url"])}" rel="nofollow">{E(d["label"] if L == "en" else DLZ[d["arch"]])}</a>'
                       for n, d in enumerate(ds if not compact else ds[:1]))
        if compact and len(ds) > 1:
            btns += f'<a class="mini" href="/{L}/{a["slug"]}/#download">{"Other chips" if L == "en" else "其他芯片"}</a>'
        return btns
    if is_mac(a):
        b = f'<a class="btn pri" href="{E(a["official_url"])}" rel="nofollow">{t["get"]}</a>'
        if a.get("repo") and not compact:
            b += f'<a class="btn sec" href="https://github.com/{E(a["repo"])}/releases/latest" rel="nofollow">{t["gh"]}</a>'
        return b
    return f'<a class="btn sec" href="{E(a["official_url"])}" rel="nofollow">{t["get"]}</a>'

def meta_line(a, L):
    t = T[L]; r = rel_of(a); bits = []
    if r.get("version"): bits.append(f'{t["ver"]} {E(r["version"])}' + (f' · {t["upd"]} {E(r["updated_at"])}' if r.get("updated_at") else ""))
    if a.get("repo"): bits.append(f'<a href="https://github.com/{E(a["repo"])}" rel="nofollow">{t["src"]}</a>')
    if a.get("license") and a["license"] not in ("NOASSERTION", "Other"): bits.append(E(a["license"]))
    return " · ".join(bits)

def tags(a, L, link=True):
    al = alts(a)
    if not al: return ""
    return f'<p class="repl"><span>{T[L]["replaces"]}</span>' + "".join(
        (f'<a class="tag" href="/{L}/alternatives/{aslug(x)}/">{E(x)}</a>' if link and x in ALTP else f'<span class="tag">{E(x)}</span>') for x in al) + "</p>"

def pitch(a, L): return a["pitch"] if L == "en" and a.get("pitch") else a[L]["one_liner"]

def card(a, L):
    grp = a.get("group") or ""
    txt = " ".join([a["name"], pitch(a, L)] + alts(a)).lower()
    return (f'<article class="card" data-g="{E(grp)}" data-t="{E(txt)}"><div class="ch"><h3><a href="/{L}/{a["slug"]}/">{E(a["name"])}</a></h3>'
            f'<span class="plat">{"Mac" if is_mac(a) else E(", ".join(a["platforms"][:3]))}</span></div><p>{E(pitch(a, L))}</p>{tags(a, L)}'
            f'<div class="acts">{dl_buttons(a, L, compact=True)}</div><p class="meta">{meta_line(a, L)}</p></article>')

def video(a, L):
    v = a.get("video")
    if not v or (v.get("live_from") or "9999") > TODAY or not v.get(L): return ""
    vid = E(v[L])
    return (f'<button class="vid" type="button" data-id="{vid}" style="background-image:url(https://i.ytimg.com/vi/{vid}/hqdefault.jpg)">'
            f'<span>▶ {T[L]["watch"]}</span></button>')

def indie(L, where, pos=None):
    out = ""
    for m in MANUAL:
        if where not in (m.get("show_on") or ["home"]): continue
        if pos and (m.get("home_position") or "top") != pos: continue
        links = "".join(f'<a class="btn {"pri" if n == 0 else "sec"}" href="{E(x["url"])}">{E(x["label"])}</a>' for n, x in enumerate(m.get("links") or []))
        c = m.get(L) or m.get("en") or {}
        out += (f'<aside class="indie"><span class="badge">{E(c.get("badge") or m.get("badge") or T[L]["featured"])}</span><h3>{E(m["name"])}</h3>'
                f'<p>{E(c.get("pitch"))}</p>' + (f'<p class="q">{E(c["quote"])}</p>' if c.get("quote") else "") +
                f'<p class="price"><b>{E(c.get("price") or m.get("price"))}</b> · {E(c.get("price_note") or m.get("price_note"))}</p><p class="muted">{E(" · ".join(m.get("platforms") or []))}</p><div class="acts">{links}</div></aside>')
    return out

def seo_title(a, L):
    al = alts(a); n = a["name"]
    if L == "zh":
        return f"{n} 是什么、怎么用" + (f"：{al[0]} 的开源平替" if al else "") + (" · Mac 官方下载" if is_mac(a) else "") + " | EasyOpenHub"
    if is_mac(a) and al: return f"{n} for Mac: No-Subscription {al[0]} Alternative | EasyOpenHub"
    if is_mac(a): return f"{n} for Mac – What It Does & Official Download | EasyOpenHub"
    if al: return f"{n}: No-Subscription {al[0]} Alternative | EasyOpenHub"
    return f"What Is {n}? What It Does & How to Get It | EasyOpenHub"

def seo_desc(a, L):
    al = alts(a)
    if L == "zh":
        return (f"{a['zh']['one_liner']}。" + (f"可替代 {'、'.join(al[:2])}，不用订阅。" if al else "") + ("Mac 官方 .dmg 直链，分 M 芯片和 Intel。" if is_mac(a) else "") + a["zh"]["what"])[:150]
    s = pitch(a, "en").rstrip(".") + "."
    if al: s += f" A no-subscription alternative to {', '.join(al[:2])}."
    if is_mac(a): s += " Direct official .dmg for Apple Silicon & Intel Macs, plus setup tips."
    return s[:158]

def item_page(a, L):
    t = T[L]; c = a[L]; p = f"/{L}/{a['slug']}/"; op = f"/{'zh' if L == 'en' else 'en'}/{a['slug']}/"
    sec = lambda h, body: f"<section><h2>{h}</h2>{body}</section>" if body else ""
    steps = "<ol>" + "".join(f"<li>{E(s)}</li>" for s in c.get("steps") or []) + "</ol>" if c.get("steps") else ""
    faq = "".join(f"<details><summary>{E(q['q'])}</summary><p>{E(q['a'])}</p></details>" for q in c.get("faq") or [])
    media = video(a, L) or (f'<img class="shot" loading="lazy" src="/{E(a["shot"])}" alt="{E(a["name"])} screenshot">' if a.get("shot") else "")
    if is_mac(a):
        dl = (f'<div class="dl" id="download"><div class="acts">{dl_buttons(a, L)}</div><p class="meta">{meta_line(a, L)}</p>'
              f'<details><summary>{t["which"]}</summary><p>{t["which_a"]}</p></details><details><summary>{t["blocked"]}</summary><p>{t["blocked_a"]}</p></details></div>')
    else:
        dl = f'<div class="dl" id="download"><p class="muted">{t["notmac"]} {E(", ".join(a["platforms"]))}</p><div class="acts">{dl_buttons(a, L)}</div><p class="meta">{meta_line(a, L)}</p></div>'
    more = "".join(f'<a href="/{L}/alternatives/{aslug(x)}/">{E(t["more_alt"].format(a=x))} →</a> ' for x in alts(a) if x in ALTP)
    body = (f'<article class="item"><p class="crumb"><a href="{t["home"]}">EasyOpenHub</a> / {E(a["name"])}</p><h1>{E(a["name"])}</h1>'
            f'<p class="lede">{E(pitch(a, L))}</p>{tags(a, L)}{dl}{media}'
            + sec(t["what"], f"<p>{E(c.get('what'))}</p>" if c.get("what") else "")
            + sec(t["good"], f"<p>{E(c.get('for'))}</p>" if c.get("for") else "")
            + sec(t["skip"], f"<p>{E(c.get('skip'))}</p>" if c.get("skip") else "")
            + sec(t["steps"], steps) + sec(t["note"], f"<p>{E(c.get('note'))}</p>" if c.get("note") else "")
            + sec(t["faq"], faq) + (f'<p class="more">{more}</p>' if more else "") + f'</article>{indie(L, "item")}')
    osn = {"Windows": "Windows", "macOS": "macOS", "Linux": "Linux", "Android": "Android", "iOS": "iOS", "Web": "Web browser"}
    r = rel_of(a)
    ld = [{"@context": "https://schema.org", "@type": "SoftwareApplication", "name": a["name"], "description": pitch(a, L),
           "applicationCategory": "UtilitiesApplication" if a["category"] != "game" else "GameApplication",
           "operatingSystem": ", ".join(osn[x] for x in a["platforms"] if x in osn),
           "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "url": BASE + p,
           "downloadUrl": (r.get("downloads") or [{}])[0].get("url") or a["official_url"],
           **({"softwareVersion": r["version"]} if r.get("version") else {}),
           **({"sameAs": f"https://github.com/{a['repo']}"} if a.get("repo") else {})}]
    if c.get("faq"):
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}} for q in c["faq"]]})
    return p, page(L, seo_title(a, L), seo_desc(a, L), p, body, op, noindex=a["status"] == "retired", ld=ld, og_img=a.get("shot"))

# ---------- alternatives ----------
by = collections.defaultdict(list)
for a in LIVE:
    for x in alts(a): by[x].append(a)
ALTP = {x: v for x, v in by.items() if len(v) >= 2 or (x in FOCUS and any(z["status"] == "priority" for z in v))}
order_key = lambda a: (a["status"] != "priority", not is_mac(a), a.get("rank") or 999, -(a.get("stars") or 0))

def alt_page(L, x, lst):
    p = f"/{L}/alternatives/{aslug(x)}/"; op = f"/{'zh' if L == 'en' else 'en'}/alternatives/{aslug(x)}/"
    lst = sorted(lst, key=order_key); mac = any(is_mac(a) for a in lst); n = len(lst)
    if L == "en":
        h = f"Best No-Subscription {x} Alternative{'s' if n > 1 else ''}{' for Mac' if mac else ''} (2026)"
        title = f"{h} | EasyOpenHub"
        desc = f"Tired of paying for {x}? {n} open-source app{'s' if n > 1 else ''} that do the same job with no subscription, compared in plain English, with direct official downloads{' for Apple Silicon & Intel Macs' if mac else ''}."
        intro = f"Tired of paying for {x}? {'These open-source apps do the same job, run on your own computer and never ask' if n > 1 else 'This open-source app does the same job, runs on your own computer and never asks'} for a monthly fee. Every download links straight to the developer’s official release."
    else:
        h = f"{x} 的 {n} 个开源平替（2026）"; title = f"{x} 平替：{n} 个不用订阅的开源软件（2026） | EasyOpenHub"
        desc = f"不想再为 {x} 每月付费？这 {n} 个开源软件能做同样的事，附中文说明和官方下载直链。"
        intro = f"不想再为 {x} 每月付费？下面的开源软件能做同样的事，装在自己电脑上，不用订阅。所有下载都直连作者官方发布。"
    cards = "".join(card(a, L) for a in lst)
    ld = [{"@context": "https://schema.org", "@type": "ItemList", "name": h, "itemListElement": [{"@type": "ListItem", "position": k + 1, "url": f"{BASE}/{L}/{a['slug']}/", "name": a["name"]} for k, a in enumerate(lst)]}]
    body = f'<p class="crumb"><a href="/{L}/alternatives/">{T[L]["nav"][1][0]}</a> / {E(x)}</p><h1>{E(h)}</h1><p class="lede">{E(intro)}</p><div class="grid">{cards}</div>{indie(L, "item")}'
    return p, page(L, title, desc, p, body, op, ld=ld)

def alt_hub(L):
    p = f"/{L}/alternatives/"; op = f"/{'zh' if L == 'en' else 'en'}/alternatives/"
    rows = sorted(ALTP.items(), key=lambda kv: (kv[0] not in FOCUS, -len(kv[1]), kv[0]))
    lis = "".join(f'<li><a href="/{L}/alternatives/{aslug(x)}/">{E(("Best " + x + " alternatives") if L == "en" else (x + " 的开源平替"))}</a> <span class="muted">({len(v)})</span></li>' for x, v in rows)
    h = "No-Subscription Alternatives to Popular Paid Apps" if L == "en" else "付费软件的开源平替"
    intro = "Pick the paid app you’re tired of paying for. Each list shows open-source apps that do the same job, with direct official downloads." if L == "en" else "选一个你不想再付费的软件，看看哪些开源软件能替代它。"
    return p, page(L, f"{h} (2026) | EasyOpenHub", intro, p, f"<h1>{E(h)}</h1><p class='lede'>{E(intro)}</p><ul class='alts'>{lis}</ul>", op)

def home(L):
    t = T[L]; p = t["home"]; op = "/zh/" if L == "en" else "/"
    if L == "en":
        hero = ('<section class="hero"><h1>Stop Paying Monthly Subscriptions.</h1><p class="lede">Curated, local-first &amp; open-source Mac apps. '
                'Direct official .dmg downloads — no GitHub hunting.</p><p class="pills"><span>Official files only</span><span>Apple Silicon &amp; Intel</span><span>No ad networks</span></p></section>')
        title = "EasyOpenHub – No-Subscription Mac Apps, Direct Official .dmg Downloads"
        desc = f"{len(PRI)} hand-picked, local-first open-source Mac apps that replace paid subscriptions like Notion, 1Password, Screen Studio and Wispr Flow. One-click official .dmg for Apple Silicon & Intel."
    else:
        hero = ('<section class="hero"><h1>别再按月给软件交钱。</h1><p class="lede">精选能装在自己 Mac 上的开源软件，官方 .dmg 一键下载，不用在 GitHub 里翻。</p>'
                '<p class="pills"><span>只链官方文件</span><span>M 芯片和 Intel 都有</span><span>不接广告联盟</span></p></section>')
        title = "EasyOpenHub 拿来就用：不用订阅的 Mac 开源软件，官方 .dmg 一键下载"
        desc = f"精选 {len(PRI)} 个能替代付费订阅的 Mac 开源软件（Notion、1Password、录屏、语音听写……），官方 .dmg 直链，分 M 芯片和 Intel。"
    chips = f'<button class="chip on" data-g="">{t["all"]}</button>' + "".join(f'<button class="chip" data-g="{E(g)}">{E(g if L == "en" else GZ[g])}</button>' for g in GROUPS)
    top_alts = [x for x in sorted(ALTP, key=lambda x: (x not in FOCUS, -len(ALTP[x])))][:14]
    repl = "".join(f'<a class="tag" href="/{L}/alternatives/{aslug(x)}/">{E(x)}</a>' for x in top_alts)
    more = "".join(f'<li><a href="/{L}/{a["slug"]}/">{E(a["name"])}</a> <span class="muted">— {E(pitch(a, L))} ({E(", ".join(a["platforms"][:3]))})</span></li>' for a in KEEP)
    body = (hero + indie(L, "home", "top") +
            f'<div class="tools"><input id="q" type="search" placeholder="{E(t["search"])}" aria-label="Search"><div class="chips">{chips}</div></div>'
            f'<div class="grid" id="grid">{"".join(card(a, L) for a in PRI)}</div><p id="none" class="muted" hidden>{"No match. Try the name of the paid app." if L == "en" else "没找到，试试付费软件的名字。"}</p>' + indie(L, "home", "after_list") +
            f'<section><h2>{t["replhdr"]}</h2><p class="repl">{repl} <a href="/{L}/alternatives/">{"All →" if L == "en" else "全部 →"}</a></p></section>'
            f'<section><h2>{t["morehdr"]}</h2><p class="muted">{t["morep"]}</p><ul class="more">{more}</ul></section>')
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "EasyOpenHub", "url": BASE + "/"}]
    return p, page(L, title, desc, p, body, op, ld=ld)

def guide(L):
    p = f"/{L}/guide/"; op = f"/{'zh' if L == 'en' else 'en'}/guide/"
    g = GUIDE[L]
    title = ("How to Install Open-Source Mac Apps Safely (.dmg, Apple Silicon vs Intel, “Can’t Be Opened”) | EasyOpenHub" if L == "en"
             else "GitHub 软件怎么下载安装？Mac .dmg、芯片选择和“无法打开”怎么办 | EasyOpenHub")
    desc = ("Which .dmg to pick for Apple Silicon or Intel, what to do when macOS says an app can’t be opened, and 8 safety checks before you install." if L == "en"
            else "M 芯片和 Intel 选哪个 .dmg、Mac 提示无法打开怎么办，以及安装前的 8 项安全检查。")
    return p, page(L, title, desc, p, f'<article class="item prose">{g}</article>', op)

def about(L):
    p = f"/{L}/about/"; op = f"/{'zh' if L == 'en' else 'en'}/about/"
    if L == "en":
        body = """<article class="item prose"><h1>Why I built EasyOpenHub</h1>
<p>Some of the best Mac apps are open source: they do what a $10-a-month subscription does, they run on your own computer, and nobody can raise the price on you. The catch is finding them. The download usually sits on GitHub, a site built for programmers, behind a page of code, a “Releases” tab and a list of files named things like <code>aarch64.dmg</code>.</p>
<p>I got tired of hunting for the right file, so I made a short list of the ones worth installing and put the right download button on each one.</p>
<h2>How downloads work (security)</h2>
<ul><li><b>Straight from the developer.</b> Every Download button points at the file the developer published in their own official GitHub release, or their official website. We don’t host, re-upload, modify or bundle anything.</li>
<li><b>Always the latest stable version.</b> A script checks each app’s latest official release every day and skips beta and pre-release builds. The version and date are shown next to every button.</li>
<li><b>No ad networks, no download wrappers.</b> Nothing stands between you and the developer’s file.</li>
<li><b>Open source is not the same as audited.</b> We pick active, well-known projects, but we don’t review their code. Read the <a href="/en/guide/">safety checklist</a> before installing anything.</li></ul>
<h2>How apps are picked</h2>
<p>An app makes the list when a regular person can install it without the command line, it runs on a Mac, it keeps your data on your own computer where possible, and it replaces something people actually pay for. Quality over quantity: apps get removed when they stop being maintained.</p>
<h2>Indie Picks</h2>
<p>Cards marked <b>Indie Pick</b> are apps made by the developer behind this site. They are clearly labeled, sold as a one-time purchase, never a subscription.</p></article>"""
        title, desc = "About EasyOpenHub & How Downloads Work (Security) | EasyOpenHub", "Why EasyOpenHub exists, how every .dmg links straight to the developer’s official release, and how apps are picked."
    else:
        body = """<article class="item prose"><h1>为什么做 EasyOpenHub</h1>
<p>很多好用的 Mac 软件是开源的：能干每月 10 美元订阅软件的活，装在自己电脑上，也没人能给你涨价。难的是找到它们。下载通常藏在 GitHub 上，那是给程序员用的网站，要翻过代码页、Releases，再从一堆叫 <code>aarch64.dmg</code> 的文件里挑对的那个。</p>
<p>我受够了一遍遍找文件，就把值得装的挑出来，每个都放上对的下载按钮。</p>
<h2>下载是怎么来的（安全）</h2>
<ul><li><b>直连作者。</b>每个下载按钮都指向作者在自己 GitHub 官方发布或官网上放的文件。本站不托管、不转存、不修改、不捆绑。</li>
<li><b>永远是最新正式版。</b>脚本每天检查每个软件的最新官方发布，跳过测试版。按钮旁边写着版本号和日期。</li>
<li><b>不接广告联盟，不套下载器。</b></li>
<li><b>开源不等于审计过。</b>我们只挑活跃、知名的项目，但不审代码。安装前请看<a href="/zh/guide/">安全清单</a>。</li></ul>
<h2>怎么选软件</h2><p>普通人不用命令行就能装、能在 Mac 上跑、尽量把数据留在自己电脑上、能替代大家真在付钱的软件。质量第一，不再维护的会被移除。</p>
<h2>作者自研</h2><p>标着「作者自研」的是本站作者自己做的软件，会明确标注，一次性买断，不搞订阅。</p></article>"""
        title, desc = "关于 EasyOpenHub 和下载安全 | EasyOpenHub", "为什么做这个网站、每个 .dmg 怎样直连作者官方发布、怎么挑软件。"
    return p, page(L, title, desc, p, body, op)

def write(path, content):
    f = D(path.lstrip("/"), "index.html") if path.endswith("/") else D(path.lstrip("/"))
    os.makedirs(os.path.dirname(f), exist_ok=True); open(f, "w").write(content)

def main():
    for d in ("en", "zh"): shutil.rmtree(D(d), ignore_errors=True)
    urls = []
    for L in ("en", "zh"):
        for fn in (home, guide, about, alt_hub):
            p, h = fn(L); write(p, h); urls.append(p)
        for x, lst in ALTP.items():
            p, h = alt_page(L, x, lst); write(p, h); urls.append(p)
        for a in APPS:
            p, h = item_page(a, L); write(p, h)
            if a["status"] != "retired": urls.append(p)
    # old URLs that no longer exist (e.g. dropped alternatives pages) -> redirect instead of 404
    old = D("scripts", "content", "old_sitemap.xml")
    made = set(urls) | {f"/{L}/{a['slug']}/" for a in APPS for L in ("en", "zh")}
    if os.path.exists(old):
        for u in re.findall(r"<loc>https://[^/]+(/[^<]*)</loc>", open(old).read()):
            if u not in made and u != "/":
                to = "/zh/alternatives/" if u.startswith("/zh/") else "/en/alternatives/"
                for suf in ("-plus/", "-pro/"):  # e.g. /en/alternatives/chatgpt/ -> /en/alternatives/chatgpt-plus/
                    if u.rstrip("/") + suf in made: to = u.rstrip("/") + suf
                write(u, f'<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><link rel="canonical" href="{BASE}{to}"><meta http-equiv="refresh" content="0;url={to}"><a href="{to}">Moved</a>')
    nf = page("en", "Page not found | EasyOpenHub", "Page not found.", "/404.html", '<h1>Page not found</h1><p class="lede">That page moved. <a href="/">Browse the Mac apps</a> or <a href="/en/alternatives/">find an alternative to a paid app</a>.</p>')
    open(D("404.html"), "w").write(nf)
    open(D("sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + "".join(f"<url><loc>{BASE}{u}</loc></url>\n" for u in dict.fromkeys(urls)) + "</urlset>\n")
    open(D("robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    open(D("llms.txt"), "w").write("# EasyOpenHub\n\n> Curated, local-first open-source Mac apps that replace paid subscriptions, each with a direct link to the developer's official .dmg (Apple Silicon / Intel / Universal), explained in plain English.\n\n"
        "- [About & security](" + BASE + "/en/about/)\n- [Install guide](" + BASE + "/en/guide/)\n- [Alternatives to paid apps](" + BASE + "/en/alternatives/)\n\n## Mac apps\n"
        + "".join(f"- [{a['name']}]({BASE}/en/{a['slug']}/): {pitch(a, 'en')}" + (f" Replaces {', '.join(alts(a))}." if alts(a) else "") + "\n" for a in PRI))
    open(D("CNAME"), "w").write(DOMAIN + "\n"); open(D(".nojekyll"), "w").write("")
    if os.path.exists(D("logo.svg")): shutil.copy(D("logo.svg"), D("favicon.svg"))
    print(f"built {len(urls)} indexed pages: {len(PRI)} priority, {len(KEEP)} keep, {len(APPS) - len(LIVE)} retired (noindex), {len(ALTP)} alternatives pages")

if __name__ == "__main__":
    main()
