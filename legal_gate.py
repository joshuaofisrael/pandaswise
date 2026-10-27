#!/usr/bin/env python3
"""PandasWise pre-publish legal-hold gate (Joshua's global rule, /workspace/content-review/RULE.md,
27 Oct 2026, with the 18:25 severity amendment).

build.py calls gate(pages) before rendering. Any held page is dropped from the build output, the blog
index, related links, sitemap.xml, llms.txt and (via --filter-urls in indexnow.sh) the IndexNow list.

A page is HELD if any of these apply and there is no valid clearance for the exact current file:
  * an explicit marker: META "status": "HOLD_REVIEW" or "<!-- status: HOLD_REVIEW -->" in the file
  * a queue.jsonl line for this site with status HOLD_REVIEW whose draft_path/source_path is this file
  * an automated check fails:
      rule 3 every <img> must have a licence record row on content/credits/index.html (no hotlinked images)
      rule 4 fact posts and pillar guides must cite at least one external source URL
      rule 1/2/6/8 keyword tripwires (allegations, private contact data, election logistics, legal notices)
Clearances:
  * HIGH (rules 1, 2, 6, 8, explicit markers, queue holds): only a line in approvals.jsonl with
    approved_by "Joshua" and sha256 equal to the exact current file. Never self-approved.
  * MODERATE automated flags (rules 3, 4 only): a moderate-clearances.jsonl line for this site with
    matching sha256 and chatgpt_verdict SAFE (bot fixed it, independent ChatGPT review agreed).

CLI:
  python3 legal_gate.py --check         scan built root HTML (<main>), sitemap.xml, llms.txt; exit 1 if held content would go out
  python3 legal_gate.py --report        list every content page with its verdict
  python3 legal_gate.py --filter-urls   read URLs on stdin, print only non-held ones (used by indexnow.sh)
  python3 legal_gate.py --scan FILE...  run the content checks on arbitrary files (drafts), no queue writes
Env overrides (tests): LEGAL_GATE_QUEUE, LEGAL_GATE_APPROVALS, LEGAL_GATE_CLEARANCES, LEGAL_GATE_DRAFTS, LEGAL_GATE_NO_QUEUE=1
"""
import os, re, sys, json, glob, hashlib, datetime, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
CR = "/workspace/content-review"
QUEUE = os.environ.get("LEGAL_GATE_QUEUE", os.path.join(CR, "queue.jsonl"))
APPROVALS = os.environ.get("LEGAL_GATE_APPROVALS", os.path.join(CR, "approvals.jsonl"))
CLEARANCES = os.environ.get("LEGAL_GATE_CLEARANCES", os.path.join(CR, "moderate-clearances.jsonl"))
DRAFTS = os.environ.get("LEGAL_GATE_DRAFTS", os.path.join(CR, "drafts", "pandaswise"))
SITE = "pandaswise.com"
SITE_ALIASES = {"pandaswise", "pandaswise.com", "PandasWise"}
BOT = "Panda Site Bot"
HIGH_RULES = {1, 2, 6, 8}
MODERATE_RULES = {3, 4, 5, 7}

# ------------------------------------------------------------------ keyword tripwires
# Deliberately NOT listed (false positives on legitimate conservation facts): poaching, poached, traps,
# illegal pet trade, trafficking of wildlife in general terms. These describe threats, not wrongdoing by
# an identifiable person or organisation. Naming a person/zoo in such a context stays a judgement call.
KW = {
    1: r"\b(fraud\w*|lawsuits?|sued|suing|indicted|indictment|arrested|convicted|charged with|criminal(ly)?|"
       r"corrupt(ion)?|embezzl\w+|brib(e|ed|es|ery)|misconduct|scam(s|med|mer)?|cover[- ]?up|negligen(t|ce)|"
       r"allegedly|accused of|abused|wrongdoing|money laundering|kickbacks?)\b",
    2: r"(\bhome address\b|\bsocial security\b|\bdate of birth\b|\bmedical records?\b|\bbank account\b|"
       r"\bprivate (email|phone|message|messages|letter)s?\b|\bleaked\b|\bdox\w*\b|"
       r"(?<![\d/.])(\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?![\d])|"
       r"\b\d{2,6}\s+[A-Z][a-z]+(\s+[A-Z][a-z]+)?\s+(Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Boulevard|Blvd|Court|Ct)\b)",
    6: r"\b(vote|votes|voting|voters?|polling (place|station|location)s?|polls? (open|close)|ballots?|"
       r"elections?|election day|register(ed)? to vote|voter registration|registration deadline|absentee|early voting)\b",
    8: r"\b(cease and desist|cease-and-desist|dmca|takedown (notice|request)|legal notice|letter before action|"
       r"copyright (complaint|claim|infringement)|infring\w+|embargo(ed)?|reporting restriction|gag order|injunction|"
       r"correction request|right to be forgotten|defamat\w+|libel\w*|slander\w*|our (lawyer|attorney|solicitor)s?)\b",
}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Allowlist (tuned 27 Oct 2026 against all 44 live content pages):
ALLOW_EMAILS = {"joshuaofisrael@gmail.com"}          # the site's own published contact / FormSubmit address
ALLOW_PHRASES = [                                    # exact phrases that are legitimate on this site
    r"Joshua Israel Ventures LLC",
]
# No page-level exemptions: the legal pages (terms, privacy, disclaimer) were scanned and trip nothing,
# so every page, including legal pages, gets every tripwire.
LEGAL_PAGES = set()

def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()

def _jsonl(path):
    out = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                try: out.append(json.loads(line))
                except ValueError: pass
    return out

def _site_ok(rec):
    return str(rec.get("site", "")).strip() in SITE_ALIASES

def credited_images():
    """File paths (img/photos/x.webp) that have a licence row on the credits page."""
    p = os.path.join(CONTENT, "credits", "index.html")
    if not os.path.exists(p): return set()
    ok = set()
    for row in re.findall(r"<tr>(.*?)</tr>", open(p, encoding="utf-8").read(), re.S):
        cells = re.findall(r"<td>(.*?)</td>", row, re.S)
        if len(cells) < 3: continue
        name = re.sub(r"<[^>]+>", "", cells[1]).strip()
        licence = re.sub(r"<[^>]+>", "", cells[-1]).strip()
        if name and licence:                      # file name + non-empty licence / "AI generated" column
            for src in re.findall(r'src="([^"]+)"', row):
                ok.add(_norm_img(src))
            ok.add("img/photos/" + name)
    return ok

def _norm_img(src):
    src = src.strip().split("?")[0]
    src = re.sub(r"^(@/|(\.\./)+|/)", "", src)
    return src

def visible_text(raw):
    """Text that will be published: tag-stripped body + META json + link/mail targets."""
    attrs = " ".join(re.findall(r'(?:href|action)="([^"]+)"', raw))
    txt = re.sub(r"<script\b.*?</script>", " ", raw, flags=re.S)
    txt = re.sub(r"<[^>]+>", " ", txt)
    return txt + " " + attrs

def keyword_flags(text, slug=""):
    flags = []
    t = text
    for ph in ALLOW_PHRASES: t = re.sub(ph, " ", t)
    for rule, pat in KW.items():
        if rule in (1, 8) and slug in LEGAL_PAGES: continue
        for m in re.finditer(pat, t, re.I if rule != 2 else 0):
            s = max(0, m.start() - 60); e = min(len(t), m.end() + 60)
            flags.append((rule, "…" + re.sub(r"\s+", " ", t[s:e]).strip() + "…"))
            break
    # rule 2 case-insensitive words (the pattern above runs case-sensitive for the street-address part)
    if not any(r == 2 for r, _ in flags):
        m = re.search(r"\b(home address|social security|date of birth|medical records?|bank account|private (email|phone|message|letter)s?|leaked|dox\w*)\b", t, re.I)
        if m: flags.append((2, "…" + t[max(0, m.start()-60):m.end()+60].strip() + "…"))
    for em in set(EMAIL_RE.findall(t)):
        if em.lower() not in ALLOW_EMAILS:
            flags.append((2, f"email address {em} (not on the site allowlist)"))
    return flags

def content_flags(meta, raw, path, credits=None, sources_table=None):
    """All automated + marker flags for one content page. Returns list of (rule, flagged, suggestion)."""
    slug = meta.get("slug", os.path.basename(path)[:-5])
    flags = []
    if str(meta.get("status", "")).upper() == "HOLD_REVIEW" or re.search(r"status\s*:\s*HOLD_REVIEW", raw, re.I):
        rules = meta.get("hold_rules") or [0]
        for r in rules:
            flags.append((int(r), "explicit status: HOLD_REVIEW marker", meta.get("hold_reason", "Held by marker; Joshua to approve this exact version.")))
    for rule, snip in keyword_flags(visible_text(raw), slug):
        sug = {1: "Possible allegation against an identifiable person/organisation. HIGH: Joshua reviews. Do not soften wording to pass.",
               2: "Possible private/sensitive personal data. HIGH: Joshua reviews, or remove the personal data entirely.",
               6: "Election logistics wording. HIGH: needs official election-authority confirmation and Joshua's review.",
               8: "Legal notice/complaint wording. HIGH: Joshua reviews; flag to Personal assistant with priority if real."}[rule]
        flags.append((rule, snip, sug))
    if slug != "credits/index":
        credits = credited_images() if credits is None else credits
        imgs = re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', raw) + \
               [u.split()[0] for s in re.findall(r'\bsrcset="([^"]+)"', raw) for u in s.split(",") if u.strip()]
        for src in sorted(set(imgs)):
            if src.startswith("data:"): continue
            if re.match(r"https?://", src):
                flags.append((3, src, "Hotlinked image: download a licensed copy and add a licence row to /credits/, or drop it."))
            elif _norm_img(src) not in credits:
                flags.append((3, src, "No licence record on /credits/: add source, author and licence row, or drop the image."))
    if meta.get("kind", "pillar") in ("post", "pillar"):
        table = sources_table or {}
        urls = [table[k][1] for k in meta.get("src", []) if k in table and re.match(r"https?://", table[k][1])]
        urls += [u for _, u in meta.get("sources", []) if re.match(r"https?://", u)]
        urls += [u for u in re.findall(r'href="(https?://[^"]+)"', raw) if "pandaswise.com" not in u]
        bad = [k for k in meta.get("src", []) if table and k not in table]
        if not urls:
            flags.append((4, "no external source URL cited", "Add at least one accessed source URL (META src/sources) before publishing."))
        if bad:
            flags.append((4, f"unknown source keys {bad}", "Fix the source keys so citations resolve."))
    return flags

def _approved(digest):
    for a in _jsonl(APPROVALS):
        if _site_ok(a) and a.get("sha256") == digest and str(a.get("approved_by", "")).strip().lower() in ("joshua", "joshua israel"):
            return True
    return False

def _moderate_cleared(digest):
    for c in _jsonl(CLEARANCES):
        if _site_ok(c) and c.get("sha256") == digest and "SAFE" in str(c.get("chatgpt_verdict", "")).upper() \
           and "UNSAFE" not in str(c.get("chatgpt_verdict", "")).upper():
            return True
    return False

def _queue_holds():
    """content paths that sit in queue.jsonl as HOLD_REVIEW for this site."""
    out = {}
    for q in _jsonl(QUEUE):
        if _site_ok(q) and q.get("status") == "HOLD_REVIEW":
            for k in ("source_path", "draft_path"):
                p = q.get(k)
                if p: out.setdefault(os.path.realpath(p), []).append(q)
    return out

def evaluate(pages, sources_table=None):
    """pages: dict slug -> meta (with 'path' and 'raw'). Returns {slug: {"flags": [...], "sha256": ..}} for held pages."""
    credits = credited_images()
    qh = _queue_holds()
    held = {}
    for slug, p in pages.items():
        path = p["path"]; digest = sha256(path)
        flags = content_flags(p, p["raw"], path, credits, sources_table)
        for q in qh.get(os.path.realpath(path), []):
            # a queued hold sticks (even after edits) until Joshua approves the exact current file
            r = q.get("rule"); r = r if isinstance(r, list) else [r]
            for x in r: flags.append((int(x) if str(x).isdigit() else 0, "listed in queue.jsonl as HOLD_REVIEW", q.get("suggestion", "")))
        if not flags: continue
        if _approved(digest):
            continue
        rules = {f[0] for f in flags}
        from_auto_only = all(f[1] not in ("listed in queue.jsonl as HOLD_REVIEW", "explicit status: HOLD_REVIEW marker") for f in flags)
        if from_auto_only and rules <= MODERATE_RULES and _moderate_cleared(digest):
            continue
        held[slug] = {"flags": flags, "sha256": digest, "path": path,
                      "severity": "HIGH" if (rules & HIGH_RULES or 0 in rules) else "MODERATE"}
    return held

def queue_held(held, pages, sources_table=None):
    """Append one queue.jsonl line per newly held item (dedup on site + source_path + sha256)."""
    if os.environ.get("LEGAL_GATE_NO_QUEUE"): return 0
    existing = {(q.get("source_path"), q.get("sha256")) for q in _jsonl(QUEUE) if _site_ok(q)}
    n = 0
    for slug, h in held.items():
        if (h["path"], h["sha256"]) in existing: continue
        os.makedirs(DRAFTS, exist_ok=True)
        draft = os.path.join(DRAFTS, slug.replace("/", "__") + ".HOLD_REVIEW.html")
        shutil.copyfile(h["path"], draft)
        p = pages[slug]
        rules = sorted({f[0] for f in h["flags"]})
        rec = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
               "site": SITE, "bot": BOT, "title": p.get("h1") or p.get("title") or slug,
               "flagged": " | ".join(f"rule {f[0]}: {f[1]}" for f in h["flags"])[:1500],
               "rule": rules[0] if len(rules) == 1 else rules,
               "sources": sorted({u for _, u in p.get("sources", [])} | set(re.findall(r'href="(https?://[^"]+)"', p["raw"]))
                                 | {(sources_table or {})[k][1] for k in p.get("src", []) if k in (sources_table or {})})[:20],
               "suggestion": " / ".join(dict.fromkeys(f[2] for f in h["flags"] if f[2]))[:1000],
               "draft_path": draft, "source_path": h["path"], "slug": slug, "sha256": h["sha256"],
               "severity": h["severity"], "status": "HOLD_REVIEW"}
        with open(QUEUE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n += 1
    return n

def gate(pages, sources_table=None, url_for=None):
    """Called by build.py. Removes held pages from `pages` in place, returns held dict."""
    for slug, p in pages.items():
        p.setdefault("path", os.path.join(CONTENT, slug + ".html"))
        p.setdefault("raw", open(p["path"], encoding="utf-8").read())
    held = evaluate(pages, sources_table)
    newq = queue_held(held, pages, sources_table)
    for slug, h in held.items():
        print(f"  [HOLD_REVIEW] {slug}: {h['severity']} rules {sorted({f[0] for f in h['flags']})} -> not built, not in sitemap/llms/IndexNow")
        for f in h["flags"]: print(f"      rule {f[0]}: {f[1][:160]}")
    for slug in held: pages.pop(slug)
    for p in pages.values():
        if p.get("related"): p["related"] = [s for s in p["related"] if s not in held]
    print(f"LEGAL GATE: {len(pages)} passed, {len(held)} held, {newq} new queue line(s)")
    return held

# ------------------------------------------------------------------ CLI helpers
def _load_content():
    sys.path.insert(0, ROOT)
    import build
    pages = build.load_pages()
    for slug, p in pages.items():
        p["path"] = os.path.join(CONTENT, slug + ".html")
        p["raw"] = open(p["path"], encoding="utf-8").read()
    return build, pages

def held_urls():
    build, pages = _load_content()
    held = evaluate(pages, build.SOURCES)
    urls = set()
    for slug in held:
        urls.add(build.url_for(slug))
        urls.add(build.BASE_URL + slug + ".html")
    return build, held, urls

def check():
    build, held, urls = held_urls()
    problems = []
    credits = credited_images()
    # 1) held pages must not exist in the built root or be referenced by sitemap/llms
    for slug in held:
        out = os.path.join(ROOT, slug + ".html")
        if os.path.exists(out): problems.append(f"held page built: {slug}.html")
    for fn in ("sitemap.xml", "llms.txt"):
        fp = os.path.join(ROOT, fn)
        txt = open(fp, encoding="utf-8").read() if os.path.exists(fp) else ""
        for u in urls:
            if re.search(re.escape(u) + r"(?=[\s<)\]#\"]|$)", txt): problems.append(f"held URL in {fn}: {u}")
        if fn == "llms.txt":
            for rule, snip in keyword_flags(txt, "llms"):
                problems.append(f"llms.txt rule {rule}: {snip[:140]}")
    # 2) every built root HTML page's <main> must itself pass the HIGH tripwires and image-licence check
    #    (catches held content forced into the output by hand, bypassing build.py)
    for fp in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        rel = os.path.relpath(fp, ROOT)
        if rel.startswith(("content/", "drafts/", "research/", "screens/", ".git/", "node_modules/")) or "/printables/" in rel:
            continue
        raw = open(fp, encoding="utf-8", errors="replace").read()
        m = re.search(r"<main>(.*)</main>", raw, re.S)
        if not m: continue
        slug = rel[:-5]
        main = m.group(1)
        main = re.sub(r'<section class="card sources">.*?</section>', " ", main, flags=re.S)
        for rule, snip in keyword_flags(visible_text(main), slug):
            problems.append(f"{rel} rule {rule}: {snip[:140]}")
        if slug != "credits/index":
            for src in set(re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', main)):
                if re.match(r"https?://", src) or _norm_img(src) not in credits:
                    problems.append(f"{rel} rule 3: image without licence record {src}")
    # approvals override: a built page whose source content file is approved by Joshua at its exact sha is fine
    approved_slugs = set()
    for fp in glob.glob(os.path.join(CONTENT, "**", "*.html"), recursive=True):
        if _approved(sha256(fp)): approved_slugs.add(os.path.relpath(fp, CONTENT)[:-5])
    problems = [p for p in problems if not any(p.startswith(s + ".html ") for s in approved_slugs)]
    if problems:
        print("LEGAL GATE CHECK FAIL: held content would be published:")
        for p in problems: print("  - " + p)
        return 1
    print(f"LEGAL GATE CHECK OK: built output, sitemap.xml and llms.txt contain no held content ({len(held)} held item(s) excluded)")
    return 0

def main(argv):
    if "--check" in argv:
        return check()
    if "--filter-urls" in argv:
        _, held, urls = held_urls()
        rc = 0
        for line in sys.stdin:
            u = line.strip()
            if not u: continue
            if u in urls:
                print(f"legal_gate: refusing held URL {u}", file=sys.stderr); rc = 0
            else:
                print(u)
        return rc
    if "--report" in argv:
        build, pages = _load_content()
        held = evaluate(pages, build.SOURCES)
        for slug in sorted(pages):
            print(("HOLD_REVIEW " if slug in held else "PASS        ") + slug +
                  ("  " + "; ".join(f"r{f[0]} {f[1][:90]}" for f in held[slug]["flags"]) if slug in held else ""))
        print(f"{len(pages) - len(held)} pass, {len(held)} held")
        return 1 if held else 0
    if "--scan" in argv:
        sys.path.insert(0, ROOT); import build
        files = argv[argv.index("--scan") + 1:]
        worst = 0
        for f in files:
            raw = open(f, encoding="utf-8", errors="replace").read()
            m = re.match(r"<!--META\s*(\{.*?\})\s*-->", raw, re.S)
            meta = json.loads(m.group(1)) if m else {"kind": "page"}
            meta["slug"] = os.path.basename(f)[:-5]
            fl = content_flags(meta, raw, f, None, build.SOURCES) if f.endswith(".html") else \
                 [(r, s, "") for r, s in keyword_flags(raw, "")]
            print(("HOLD_REVIEW " if fl else "PASS        ") + f)
            for r, s, _ in fl: print(f"    rule {r}: {s[:160]}")
            worst = max(worst, 1 if fl else 0)
        return worst
    print(__doc__); return 2

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
