#!/usr/bin/env python3
"""PandasWise static site builder.

Renders content/*.html fragments into static HTML at the repo root (GitHub Pages
"Deploy from a branch", main, root). No dependencies beyond the Python standard library.

To move to a custom domain later: change BASE_URL below (one line), add a CNAME file
containing the bare domain, run `python3 build.py`, commit and push, then ping IndexNow.
"""
import json, os, re, html, glob, datetime

# ---------------------------------------------------------------- configuration
BASE_URL = "https://pandaswise.com/"   # <- the ONE line to change for a custom domain
SITE = "PandasWise"
LEGAL = "Joshua Israel Ventures LLC"
GSC_TOKEN = ""        # Google Search Console HTML tag token (content="...") once Joshua adds the property
CF_BEACON_TOKEN = "5291cdd89aa34aebb1c001ba61b8a0e0"  # Cloudflare Web Analytics beacon token, once a site exists for this hostname
CONTACT_EMAIL = "joshuaofisrael@gmail.com"  # FormSubmit endpoint owner (shared JI Ventures inbox)
ROOT = os.path.dirname(os.path.abspath(__file__))
INDEXNOW_KEY = open(os.path.join(ROOT, ".indexnow_key")).read().strip()
BASE_PATH = re.sub(r"^https?://[^/]+", "", BASE_URL)  # "/pandaswise/" now, "/" on a custom domain
HOST = re.sub(r"^https?://([^/]+).*$", r"\1", BASE_URL)
OG_IMAGE = BASE_URL + "og.png"

NAV = [("index", "Home"), ("where-to-see-pandas", "Where to See Pandas"), ("giant-panda", "Giant Panda"),
       ("red-panda", "Red Panda"), ("diet", "Diet"), ("behavior", "Behavior"), ("habitat", "Habitat"),
       ("conservation", "Conservation"),
       ("giant-vs-red-panda", "Giant vs Red"), ("faq", "FAQ"), ("glossary", "Glossary"),
       ("blog/index", "Blog"), ("games/index", "Games"), ("teachers/index", "Teachers")]

LOGO = ('<svg role="img" width="36" height="36" viewBox="0 0 64 64" aria-labelledby="logo-t">'
        '<title id="logo-t">PandasWise logo</title>'
        '<circle cx="15" cy="17" r="9" fill="#2b2f2c"/><circle cx="49" cy="17" r="9" fill="#2b2f2c"/>'
        '<circle cx="32" cy="35" r="23" fill="#fff" stroke="#2b2f2c" stroke-width="2"/>'
        '<ellipse cx="23" cy="33" rx="6" ry="8" transform="rotate(-25 23 33)" fill="#2b2f2c"/>'
        '<ellipse cx="41" cy="33" rx="6" ry="8" transform="rotate(25 41 33)" fill="#2b2f2c"/>'
        '<circle cx="24" cy="32" r="2" fill="#fff"/><circle cx="40" cy="32" r="2" fill="#fff"/>'
        '<ellipse cx="32" cy="44" rx="4" ry="3" fill="#2b2f2c"/>'
        '<path d="M50 60 C56 50 60 44 62 34" stroke="#7cc45a" stroke-width="3" fill="none"/>'
        '<path d="M58 44 C52 42 50 38 51 34 C56 36 58 40 58 44Z" fill="#7cc45a"/></svg>')


SOURCES = {
 "iucn-giant": ("IUCN Red List: Giant panda, Ailuropoda melanoleuca (2016 assessment)", "https://www.iucnredlist.org/species/712/121745669"),
 "iucn-red": ("IUCN Red List: Red panda, Ailurus fulgens (2015 assessment)", "https://www.iucnredlist.org/species/714/110023718"),
 "si-giant": ("Smithsonian's National Zoo and Conservation Biology Institute: Giant panda", "https://nationalzoo.si.edu/animals/giant-panda"),
 "si-red": ("Smithsonian's National Zoo and Conservation Biology Institute: Red panda", "https://nationalzoo.si.edu/animals/red-panda"),
 "sdz-giant": ("San Diego Zoo Wildlife Alliance, Animals and Plants: Giant panda", "https://animals.sandiegozoo.org/animals/giant-panda"),
 "sdz-red": ("San Diego Zoo Wildlife Alliance, Animals and Plants: Red panda", "https://animals.sandiegozoo.org/animals/red-panda"),
 "sdz-red-fs": ("San Diego Zoo Wildlife Alliance Library: Red panda fact sheet, population and conservation status", "https://ielc.libguides.com/sdzg/factsheets/redpanda/population"),
 "wwf-giant": ("WWF: Giant panda", "https://www.worldwildlife.org/species/giant-panda"),
 "wwf-red": ("WWF: Red panda", "https://www.worldwildlife.org/species/red-panda"),
 "hu2020": ("Hu et al. (2020), Genomic evidence for two phylogenetic species and long term population bottlenecks in red pandas, Science Advances", "https://www.science.org/doi/10.1126/sciadv.aax5751"),
 "nie2015": ("Nie et al. (2015), Exceptionally low daily energy expenditure in the bamboo eating giant panda, Science", "https://www.science.org/doi/10.1126/science.aab2413"),
 "caro2017": ("Caro et al. (2017), Why is the giant panda black and white?, Behavioral Ecology", "https://academic.oup.com/beheco/article/28/3/657/3058530"),
 "ucdavis": ("UC Davis news: Why pandas are black and white", "https://www.ucdavis.edu/news/why-pandas-are-black-and-white-answered"),
 "xinhua-2026": ("Xinhua (14 June 2026): China's systematic push powers panda protection", "https://english.news.cn/20260614/1408bb65ae534b58b62bed4e5b74e01a/c.html"),
 "xinhua-park": ("Xinhua (23 November 2025): National park boosts panda population", "https://english.news.cn/20251123/b5a4098b763f4f9e896a507f5e0e90ef/c.html"),
 "bbc-2021": ("BBC News (2021): Giant pandas no longer endangered but still vulnerable, says China", "https://www.bbc.co.uk/news/world-asia-china-57773472"),
 "endo1999": ("Endo et al. (1999), Role of the giant panda's pseudo thumb, Nature 397: 309 to 310. DOI 10.1038/16830", "https://doi.org/10.1038/16830"),
 "salesa2006": ("Salesa et al. (2006), Evidence of a false thumb in a fossil carnivore clarifies the evolution of pandas, PNAS 103: 379 to 382. DOI 10.1073/pnas.0504899102", "https://doi.org/10.1073/pnas.0504899102"),
 "wang2022": ("Wang et al. (2022), Earliest giant panda false thumb suggests conflicting demands for locomotion and feeding, Scientific Reports 12. DOI 10.1038/s41598-022-13402-y", "https://doi.org/10.1038/s41598-022-13402-y"),
 "unesco": ("UNESCO World Heritage Centre: Sichuan Giant Panda Sanctuaries", "https://whc.unesco.org/en/list/1213"),
 "chengdu": ("Chengdu Research Base of Giant Panda Breeding (official site)", "https://www.panda.org.cn/en/"),
 "tian2019": ("Tian et al. (2019), The next widespread bamboo flowering poses a massive risk to the giant panda, Biological Conservation (PDF, Michigan State University)", "https://www.canr.msu.edu/csis/uploads/files/Tian%20et%20al%202019%20Bamboo%20flowering%20and%20Pandas.pdf"),
 "psu-bamboo": ("Penn State University: Peace and bamboo (research story on pandas and bamboo die off)", "https://www.psu.edu/news/research/story/peace-and-bamboo"),
 "jabs": ("Journal of the American Bamboo Society, vol. 4 (PDF): bamboo flowering and giant panda starvation in the Min Shan, 1974 to 1976", "https://bamboo.org/_uploads/pdfs/JABSv04.pdf"),
 "rpn-eco": ("Red Panda Network: Ecotrip FAQs", "https://redpandanetwork.org/ecotrip-faqs"),
 "bista2022esr": ("Bista et al. (2022), Space use, interaction and recursion in a solitary specialized herbivore: a red panda case study, Endangered Species Research 47: 131 to 143. DOI 10.3354/esr01171", "https://doi.org/10.3354/esr01171"),
 "bista2022le": ("Bista et al. (2022), Effect of disturbances and habitat fragmentation on an arboreal habitat specialist mammal using GPS telemetry: a case of the red panda, Landscape Ecology 37: 795 to 809. DOI 10.1007/s10980-021-01357-w", "https://doi.org/10.1007/s10980-021-01357-w"),
 "thapa2018": ("Thapa et al. (2018), Predicting the potential distribution of the endangered red panda across its entire range using MaxEnt modeling, Ecology and Evolution 8(21). DOI 10.1002/ece3.4526", "https://doi.org/10.1002/ece3.4526"),
 "bista2017": ("Bista et al. (2017), Distribution and habitat use of red panda in the Chitwan Annapurna Landscape of Nepal, PLOS ONE 12(10). DOI 10.1371/journal.pone.0178797", "https://doi.org/10.1371/journal.pone.0178797"),
 "panthi2017": ("Panthi et al. (2017), Large anthropogenic impacts on a charismatic small carnivore: Insights from distribution surveys of red panda Ailurus fulgens in Nepal, PLOS ONE. DOI 10.1371/journal.pone.0180978", "https://doi.org/10.1371/journal.pone.0180978"),
 "lismith2020": ("Li, P. and Smith, K. K. (2020), Comparative skeletal anatomy of neonatal ursids and the extreme altriciality of the giant panda, Journal of Anatomy 236(4): 724 to 736. DOI 10.1111/joa.13127", "https://doi.org/10.1111/joa.13127"),
 "zhu2001": ("Zhu, X., Lindburg, D. G., Pan, W., Forney, K. A. and Wang, D. (2001), The reproductive strategy of giant pandas (Ailuropoda melanoleuca): infant growth and development and mother infant relationships, Journal of Zoology 253(2): 141 to 155. DOI 10.1017/S0952836901000139", "https://doi.org/10.1017/S0952836901000139"),
 "spady2007": ("Spady, T. J., Lindburg, D. G. and Durrant, B. S. (2007), Evolution of reproductive seasonality in bears, Mammal Review 37(1): 21 to 53. DOI 10.1111/j.1365-2907.2007.00096.x", "https://doi.org/10.1111/j.1365-2907.2007.00096.x"),
 "zhao2010": ("Zhao, H., Yang, J. R., Xu, H. and Zhang, J. (2010), Pseudogenization of the umami taste receptor gene Tas1r1 in the giant panda coincided with its dietary switch to bamboo, Molecular Biology and Evolution 27(12): 2669 to 2673. DOI 10.1093/molbev/msq153", "https://doi.org/10.1093/molbev/msq153"),
 "li2010": ("Li, R., Fan, W., Tian, G., Zhu, H., He, L., Cai, J. et al. (2010), The sequence and de novo assembly of the giant panda genome, Nature 463(7279): 311 to 317. DOI 10.1038/nature08696", "https://doi.org/10.1038/nature08696"),
 "xue2015": ("Xue, Z., Zhang, W., Wang, L., Hou, R., Zhang, M., Fei, L. et al. (2015), The bamboo eating giant panda harbors a carnivore like gut microbiota, with excessive seasonal variations, mBio 6(3). DOI 10.1128/mBio.00022-15", "https://doi.org/10.1128/mBio.00022-15"),
 "fei2017": ("Fei, Y., Hou, R., Spotila, J. R., Paladino, F. V., Qi, D. and Zhang, Z. (2017), Metabolic rate of the red panda, Ailurus fulgens, a dietary bamboo specialist, PLOS ONE 12(3): e0173274. DOI 10.1371/journal.pone.0173274", "https://doi.org/10.1371/journal.pone.0173274"),
 "mcnab1988": ("McNab, B. K. (1988), Energy conservation in a tree kangaroo (Dendrolagus matschiei) and the red panda (Ailurus fulgens), Physiological Zoology 61(3): 280 to 292. DOI 10.1086/physzool.61.3.30161241", "https://doi.org/10.1086/physzool.61.3.30161241"),
 "zhang2009": ("Zhang, H., Li, D., Wang, C. and Hull, V. (2009), Delayed implantation in giant pandas: the first comprehensive empirical evidence, Reproduction 138(6): 979 to 986. DOI 10.1530/rep-09-0241", "https://doi.org/10.1530/rep-09-0241"),
 "wauters2023": ("Wauters, J., Wilson, K. S., Cools, T., Vancsok, C., Bouts, T., Mulot, B., Leclerc, A., Haapakoski, M. et al. (2023), Pregnancy length and health in giant pandas: What can metabolic and urinary endocrine markers unveil?, Theriogenology Wild 3: 100063. DOI 10.1016/j.therwi.2023.100063", "https://doi.org/10.1016/j.therwi.2023.100063"),
 "cools2025": ("Cools, T., Wilson, K. S., Li, D., Vancsok, C., Mulot, B., Leclerc, A. et al. (2025), Non-invasive giant panda pregnancy and pseudopregnancy biomonitoring by integrated metabolomics and steroidomics, Scientific Reports. DOI 10.1038/s41598-025-19067-7", "https://doi.org/10.1038/s41598-025-19067-7"),
 "luo2025": ("Luo, Y., Yang, Z., Zhou, X., Li, D., Lai, L., Zeng, C. et al. (2025), Exploring Captive Giant Panda Reproduction: Maternal and Offspring Factor Correlations from 324 Breeding Events, Animals 15(8): 1182. DOI 10.3390/ani15081182", "https://doi.org/10.3390/ani15081182"),
 "darjeeling": ("Padmaja Naidu Himalayan Zoological Park, Darjeeling (official site)", "https://www.darjeelingzoo.in/"),
 "wei1999": ("Wei, F., Feng, Z., Wang, Z., Zhou, A. and Hu, J. (1999), Use of the nutrients in bamboo by the red panda (Ailurus fulgens), Journal of Zoology 248: 535 to 541. DOI 10.1111/j.1469-7998.1999.tb01053.x", "https://doi.org/10.1111/j.1469-7998.1999.tb01053.x"),
 "hu2017": ("Hu, Y., Wu, Q., Ma, S. et al. (2017), Comparative genomics reveals convergent evolution between the bamboo eating giant and red pandas, Proceedings of the National Academy of Sciences 114: 1081 to 1086. DOI 10.1073/pnas.1613870114", "https://doi.org/10.1073/pnas.1613870114"),
 "reid1991": ("Reid, D. G., Hu, J. and Huang, Y. (1991), Ecology of the red panda Ailurus fulgens in the Wolong Reserve, China, Journal of Zoology 225(3): 347 to 364. DOI 10.1111/j.1469-7998.1991.tb03821.x", "https://doi.org/10.1111/j.1469-7998.1991.tb03821.x"),
 "bugler2023": ("Bugler, K., Ross, J. and Paterson, A. (2023), Activity patterns of captive red panda (Ailurus fulgens), Animals 13(5): 846. DOI 10.3390/ani13050846", "https://doi.org/10.3390/ani13050846"),
 "white2002": ("White, A. M., Swaisgood, R. R. and Zhang, H. (2002), The highs and lows of chemical communication in giant pandas (Ailuropoda melanoleuca): effect of scent deposition height on signal discrimination, Behavioral Ecology and Sociobiology 51: 519 to 529. DOI 10.1007/s00265-002-0473-3", "https://doi.org/10.1007/s00265-002-0473-3"),
 "swaisgood1999": ("Swaisgood, R. R., Lindburg, D. G. and Zhou, X. (1999), Giant pandas discriminate individual differences in conspecific scent, Animal Behaviour 57: 1045 to 1053. DOI 10.1006/anbe.1998.1070", "https://doi.org/10.1006/anbe.1998.1070"),
 "christiansen2007": ("Christiansen, P. (2007), Evolutionary implications of bite mechanics and feeding ecology in bears, Journal of Zoology 272: 423 to 443. DOI 10.1111/j.1469-7998.2006.00286.x", "https://doi.org/10.1111/j.1469-7998.2006.00286.x"),
 "christiansenwroe2007": ("Christiansen, P. and Wroe, S. (2007), Bite forces and evolutionary adaptations to feeding ecology in carnivores, Ecology 88: 347 to 358. DOI 10.1890/0012-9658(2007)88[347:BFAEAT]2.0.CO;2", "https://doi.org/10.1890/0012-9658(2007)88[347:BFAEAT]2.0.CO;2"),
 "figueirido2013": ("Figueirido, B., Tseng, Z. J. and Martin Serra, A. (2013), Skull shape evolution in durophagous carnivorans, Evolution 67: 1975 to 1993. DOI 10.1111/evo.12059", "https://doi.org/10.1111/evo.12059"),
 "charlton2009": ("Charlton, B. D., Zhang, Z. and Snyder, R. J. (2009), The information content of giant panda, Ailuropoda melanoleuca, bleats: acoustic cues to sex, age and size, Animal Behaviour 78: 893 to 898. DOI 10.1016/j.anbehav.2009.06.029", "https://doi.org/10.1016/j.anbehav.2009.06.029"),
 "charlton2010": ("Charlton, B. D., Keating, J. L., Kersey, D., Rengui, L. et al. (2011), Vocal cues to male androgen levels in giant pandas, Biology Letters 7(1): 71 to 74. DOI 10.1098/rsbl.2010.0582", "https://doi.org/10.1098/rsbl.2010.0582"),
 "johnson1988": ("Johnson, K. G., Schaller, G. B. and Hu, J. (1988), Comparative behavior of red and giant pandas in the Wolong Reserve, China, Journal of Mammalogy 69(3): 552 to 564. DOI 10.2307/1381347", "https://doi.org/10.2307/1381347"),
 "zhang2015": ("Zhang, J., Hull, V., Huang, J., Zhou, S., Xu, W., Yang, H. et al. (2015), Activity patterns of the giant panda (Ailuropoda melanoleuca), Journal of Mammalogy 96(6): 1116 to 1127. DOI 10.1093/jmammal/gyv118", "https://doi.org/10.1093/jmammal/gyv118"),
 "zhang2018": ("Zhang, M., Zhang, Z., Li, Z., Hong, M., Zhou, X., Zhou, S. et al. (2018), Giant panda foraging and movement patterns in response to bamboo shoot growth, Environmental Science and Pollution Research 25(9): 8636 to 8643. DOI 10.1007/s11356-017-0919-9", "https://doi.org/10.1007/s11356-017-0919-9"),
}

ORG = {"@type": "Organization", "@id": BASE_URL + "#organization", "name": SITE,
       "url": BASE_URL, "logo": BASE_URL + "logo.png", "email": "joshuaofisrael@gmail.com",
       "brand": {"@type": "Brand", "name": SITE, "url": BASE_URL, "logo": BASE_URL + "logo.png"}}

def esc(s): return html.escape(s, quote=True)

def url_for(slug):
    if slug == "index": return BASE_URL
    if slug.endswith("/index"): return BASE_URL + slug[:-5]
    return BASE_URL + slug + ".html"

def rel_href(slug, depth):
    pre = "../" * depth
    if slug == "index": return pre + "index.html" if depth else "index.html"
    if slug.endswith("/index"): return pre + slug[:-5]
    return pre + slug + ".html"

def load_pages():
    pages = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "content", "**", "*.html"), recursive=True)):
        slug = os.path.relpath(path, os.path.join(ROOT, "content"))[:-5]
        raw = open(path, encoding="utf-8").read()
        m = re.match(r"<!--META\s*(\{.*?\})\s*-->\s*", raw, re.S)
        if not m: raise SystemExit("missing META in " + path)
        meta = json.loads(m.group(1))
        meta["slug"] = slug
        meta["body"] = raw[m.end():]
        meta.setdefault("kind", "pillar")
        meta.setdefault("short", meta.get("h1", slug))
        pages[slug] = meta
    return pages

def ld(obj):
    obj = dict(obj); obj.setdefault("@context", "https://schema.org")
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"

def fmt_date(d):
    return datetime.date.fromisoformat(d).strftime("%-d %B %Y")

def fmt_mla_date(d):
    return datetime.date.fromisoformat(d).strftime("%-d %b. %Y")

def cite_box(p, canon):
    """APA, MLA and Chicago cite strings for fact articles and pillars."""
    h1 = p["h1"]
    year = p["published"][:4]
    apa_date = datetime.date.fromisoformat(p["published"]).strftime("%Y, %B %-d")
    mla_date = fmt_mla_date(p["published"])
    chi_date = datetime.date.fromisoformat(p["published"]).strftime("%B %-d, %Y")
    end = "" if h1.rstrip().endswith(("?", "!")) else "."
    apa = f"{SITE}. ({apa_date}). {h1}{end} {canon}"
    mla = f'"{h1}{end}" {SITE}, {mla_date}, {canon}.'
    chicago = f'{SITE}. "{h1}{end}" {SITE}. {chi_date}. {canon}.'
    return (
        '<section class="card cite" id="cite"><h2>Cite this page</h2>'
        f'<p><strong>APA</strong><br>{esc(apa)}</p>'
        f'<p><strong>MLA</strong><br>{esc(mla)}</p>'
        f'<p><strong>Chicago</strong><br>{esc(chicago)}</p></section>'
    )

def render(p, pages):
    slug, depth = p["slug"], p["slug"].count("/")
    R = "../" * depth
    canon = url_for(slug)
    title = p["title"]; desc = p["description"]
    head = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
            '<meta name="google-site-verification" content="SlAoHf98mQg1jLj8BBYeGs96y_9dN3978x2ziFQL58k" /><meta name="msvalidate.01" content="942EB99DB458637348E2ADBDEBDAA7AE" />',
            '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5681559774142917" crossorigin="anonymous"></script><meta name="google-adsense-account" content="ca-pub-5681559774142917">',
            '<meta name="viewport" content="width=device-width,initial-scale=1">']
    if slug == "index" and GSC_TOKEN:
        head.append(f'<meta name="google-site-verification" content="{esc(GSC_TOKEN)}">')
    head += [f"<title>{esc(title)}</title>", f'<meta name="description" content="{esc(desc)}">']
    if p.get("noindex"): head.append('<meta name="robots" content="noindex">')
    else: head.append(f'<link rel="canonical" href="{canon}">')
    head += ['<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800&display=swap">',
             f'<link rel="stylesheet" href="{R}style.css">',
             f'<link rel="icon" href="{R}favicon.svg" type="image/svg+xml">',
             f'<meta property="og:type" content="{"website" if p["kind"] in ("home","page","blog_index") else "article"}">',
             f'<meta property="og:site_name" content="{SITE}">',
             f'<meta property="og:title" content="{esc(title)}">',
             f'<meta property="og:description" content="{esc(desc)}">',
             f'<meta property="og:url" content="{canon}">',
             f'<meta property="og:image" content="{OG_IMAGE}">',
             '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
             '<meta name="twitter:card" content="summary_large_image">']
    # structured data
    if p["kind"] == "home":
        head.append(ld({"@type": "WebSite", "name": SITE, "url": BASE_URL, "inLanguage": "en",
                        "publisher": ORG}))
        head.append(ld(ORG))
    crumbs = []
    if slug != "index":
        crumbs = [("Home", "index")]
        if slug.startswith("blog/") and slug != "blog/index": crumbs.append(("Blog", "blog/index"))
        crumbs.append((p["short"], slug))
        head.append(ld({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": url_for(s)}
            for i, (n, s) in enumerate(crumbs)]}))
    if p["kind"] in ("pillar", "post"):
        head.append(ld({"@type": "BlogPosting" if p["kind"] == "post" else "Article",
                        "headline": p["h1"], "description": desc, "image": OG_IMAGE,
                        "datePublished": p["published"], "dateModified": p["modified"],
                        "author": ORG, "publisher": ORG, "mainEntityOfPage": canon,
                        "inLanguage": "en"}))
    elif p["kind"] == "page":
        page_ld = {"@type": p.get("schema", "WebPage"), "name": p["h1"], "url": canon,
                   "description": desc, "publisher": ORG}
        if p.get("educationalLevel"):
            page_ld["educationalLevel"] = p["educationalLevel"]
        if p.get("learningResourceType"):
            page_ld["learningResourceType"] = p["learningResourceType"]
        if p.get("schema") == "LearningResource":
            page_ld["isAccessibleForFree"] = True
            page_ld["inLanguage"] = "en"
        head.append(ld(page_ld))
    if p.get("faq"):
        head.append(ld({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer",
             "text": re.sub(r"<[^>]+>", "", a)}} for q, a in p["faq"]]}))
    head.append("</head><body>")
    # header + nav
    nav_cur = p.get("nav", slug)
    nav = "".join(f'<a href="{rel_href(s, depth)}"{" aria-current=page" if s == nav_cur else ""}>{n}</a>'
                  for s, n in NAV)
    out = head + [f'<header><a class="brand" href="{rel_href("index", depth)}">{LOGO}<span>{SITE}</span></a>'
                  '<button class="menu" aria-label="Menu" onclick="document.body.classList.toggle(\'open\')">&#9776;</button>'
                  f"<nav>{nav}</nav></header><main>"]
    if crumbs:
        out.append('<nav class="crumbs" aria-label="Breadcrumb">' + " &rsaquo; ".join(
            f'<a href="{rel_href(s, depth)}">{esc(n)}</a>' if i < len(crumbs) - 1 else f"<span>{esc(n)}</span>"
            for i, (n, s) in enumerate(crumbs)) + "</nav>")
    body = p["body"].replace("@/", R)
    body = body.replace("{{ANALYTICS}}", (
        "PandasWise uses cookieless Cloudflare Web Analytics to count page views. It does not use cookies or local storage and does not "
        "collect personal data to track you across sites. It records anonymous information such as the page visited, "
        "referrer, browser type and country.") if CF_BEACON_TOKEN else (
        "PandasWise does not currently run any analytics. We may add Cloudflare Web Analytics, which does not use cookies; "
        "if we do, we will update this policy before it goes live."))
    if p["kind"] in ("pillar", "post", "page", "blog_index"):
        out.append(f'<h1>{esc(p["h1"])}</h1>')
        if p["kind"] in ("pillar", "post"):
            pub = fmt_date(p["published"]); mod = fmt_date(p["modified"])
            rev = fmt_date(p.get("reviewed", p["modified"]))
            line = f'Published {pub} &middot; Last updated {mod} &middot; Last reviewed {rev}'
            out.append(f'<p class="meta">{line} &middot; By the {SITE} team</p>')
    if p["kind"] == "blog_index":
        posts = sorted([q for q in pages.values() if q["kind"] == "post"],
                       key=lambda q: (q["published"], q["h1"]), reverse=True)
        body = body.replace("{{POSTS}}", "".join(
            f'<article class="card post-card"><h2><a href="{rel_href(q["slug"], depth)}">{esc(q["h1"])}</a></h2>'
            f'<p class="meta">{fmt_date(q["published"])}</p><p>{esc(q["description"])}</p></article>' for q in posts))
    out.append(body)
    if p.get("faq"):
        out.append('<section class="card faq" id="faq"><h2>' + esc(p.get("faq_title", "Frequently asked questions")) + "</h2>")
        for q, a in p["faq"]:
            out.append(f"<h3>{esc(q)}</h3><p>{a.replace('@/', R)}</p>")
        out.append("</section>")
    if p.get("related"):
        out.append('<section class="card related"><h2>Related guides</h2><ul>' + "".join(
            f'<li><a href="{rel_href(s, depth)}">{esc(pages[s].get("link_text", pages[s]["h1"]))}</a></li>'
            for s in p["related"]) + "</ul></section>")
    srcs = [SOURCES[k] for k in p.get("src", [])] + [tuple(x) for x in p.get("sources", [])]
    if srcs:
        p = dict(p, sources=srcs)
    if p.get("sources"):
        out.append('<section class="card sources"><h2>Sources</h2><ol>' + "".join(
            f'<li><a href="{esc(u)}" rel="noopener">{esc(n)}</a></li>' for n, u in p["sources"]) + "</ol></section>")
    if p["kind"] in ("pillar", "post"):
        out.append(cite_box(p, canon))
    out.append("</main>")
    out.append(f'<footer><section class="contact-us" aria-labelledby="contact-us-h"><h2 id="contact-us-h">Contact us</h2>'
               f'<p>Questions, corrections or suggestions? Please use our <a href="{rel_href("contact", depth)}">contact form</a>.</p></section>')
    legal_line = (f'<p class="op">&copy; 2026 {LEGAL}. All rights reserved. {SITE} is a trade name of {LEGAL}, a Florida limited liability company.</p>'
                  if p.get("slug") in ("terms", "privacy", "disclaimer") else "")
    out.append(legal_line + f'<p class="flinks"><a href="{rel_href("terms", depth)}">Terms</a> &middot; <a href="{rel_href("privacy", depth)}">Privacy</a>'
               f' &middot; <a href="{rel_href("disclaimer", depth)}">Disclaimer</a> &middot; <a href="{rel_href("contact", depth)}">Contact</a>'
               f' &middot; <a href="{rel_href("about", depth)}">About</a> &middot; <a href="{rel_href("blog/index", depth)}">Blog</a></p>'
               f'<p>{SITE}: original educational content about giant pandas and red pandas. All text is original. Real photos and AI generated images (always labelled) are credited on our <a href="{R}credits/">photo credits</a> page.</p></footer>')
    if CF_BEACON_TOKEN:
        out.append("<!-- Cloudflare Web Analytics --><script defer src='https://static.cloudflareinsights.com/beacon.min.js' "
                   f"data-cf-beacon='{{\"token\": \"{CF_BEACON_TOKEN}\"}}'></script><!-- End Cloudflare Web Analytics -->")
    out.append("</body></html>\n")
    return "\n".join(out)

def build():
    pages = load_pages()
    for p in pages.values():
        for s in p.get("related", []):
            if s not in pages: raise SystemExit(f"{p['slug']}: unknown related slug {s}")
        dst = os.path.join(ROOT, p["slug"] + ".html")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "w", encoding="utf-8").write(render(p, pages))
    # 404 (absolute links, noindex)
    nf = render({"slug": "404", "kind": "page", "title": f"Page not found | {SITE}", "noindex": True,
                 "description": "This page could not be found.", "h1": "Page not found", "short": "Not found",
                 "body": '<p class="lead">Sorry, that page does not exist. Try the <a href="@/index.html">PandasWise home page</a>, '
                         'the <a href="@/giant-panda.html">giant panda guide</a> or the <a href="@/where-to-see-pandas.html">list of zoos with pandas</a>.</p>'},
                pages)
    nf = re.sub(r'(href|src)="(?!https?:|#|/)([^"]*)"', lambda m: f'{m.group(1)}="{BASE_PATH}{m.group(2)}"', nf)
    nf = re.sub(r'<script type="application/ld\+json"[^>]*>.*?</script>', "", nf)  # no schema on 404
    open(os.path.join(ROOT, "404.html"), "w").write(nf)
    # sitemap
    idx = [p for p in pages.values() if not p.get("noindex")]
    order = [s for s, _ in NAV] + ["about", "contact", "terms", "privacy", "disclaimer"]
    idx.sort(key=lambda p: (order.index(p["slug"]) if p["slug"] in order else 100, p["slug"]))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in idx:
        sm.append(f'  <url><loc>{url_for(p["slug"])}</loc><lastmod>{p.get("modified", p.get("published", "2026-10-08"))}</lastmod></url>')
    sm.append(f"  <url><loc>{BASE_URL}llms.txt</loc><lastmod>{max(p.get('modified','2026-10-08') for p in idx)}</lastmod></url>")
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
    # robots
    bots = ["Googlebot", "Bingbot", "OAI-SearchBot", "ChatGPT-User", "GPTBot", "PerplexityBot", "Perplexity-User",
            "ClaudeBot", "Claude-SearchBot", "Claude-User", "Google-Extended", "Applebot", "Applebot-Extended",
            "DuckAssistBot", "Amazonbot", "anthropic-ai", "CCBot", "Bytespider", "Meta-ExternalAgent", "cohere-ai"]
    rb = ["User-agent: *", "Allow: /", ""] + sum([[f"User-agent: {b}", "Allow: /", ""] for b in bots], [])
    rb.append(f"Sitemap: {BASE_URL}sitemap.xml")
    open(os.path.join(ROOT, "robots.txt"), "w").write("\n".join(rb) + "\n")
    # llms.txt
    def item(s): return f"- [{pages[s].get('link_text', pages[s]['h1'])}]({url_for(s)}): {pages[s]['description']}"
    guides = ["giant-panda", "red-panda", "diet", "behavior", "habitat", "conservation", "giant-vs-red-panda", "faq", "glossary"]
    posts = sorted([p["slug"] for p in pages.values() if p["kind"] == "post"])
    w = url_for("where-to-see-pandas")
    L = [f"# {SITE}", "",
         f"> {SITE} is a free, original educational website about giant pandas (Ailuropoda melanoleuca) and red pandas "
         "(Ailurus). It explains panda biology, diet, behavior, habitat, conservation status and how the two species differ, "
         "and keeps a verified, country by country list of zoos and reserves where giant pandas and red pandas can be seen, each entry checked against an official page with a last verified date. "
         "", 
         "Content is general education written from cited sources (IUCN, WWF, Smithsonian's National Zoo, San Diego Zoo "
         "Wildlife Alliance, peer reviewed studies and official zoo announcements). Zoo details change; check with the zoo before visiting.",
         "", "## Guides"] + [item(s) for s in guides] + [
         "", "## Tools",
         item("where-to-see-pandas"),
         item("games/index"), item("games/bamboo-breakfast/index"), item("games/which-panda-is-it/index"), item("teachers/index"), item("researchers/index"),
         f"  - Sections: [Giant pandas by country]({w}#outside-china), [Giant pandas in China]({w}#china), "
         f"[Red pandas by country]({w}#red-pandas), [Countries with no giant pandas now]({w}#none-now)",
         "", "## Blog"] + [item(s) for s in posts] + [
         "", "## Optional", item("about"), item("contact"), item("terms"), item("privacy"), item("disclaimer")]
    open(os.path.join(ROOT, "llms.txt"), "w").write("\n".join(L) + "\n")
    # IndexNow key file
    open(os.path.join(ROOT, INDEXNOW_KEY + ".txt"), "w").write(INDEXNOW_KEY)
    host = re.sub(r"^https?://([^/]+).*$", r"\1", BASE_URL)
    cname = os.path.join(ROOT, "CNAME")
    if host.endswith("github.io"):
        if os.path.exists(cname): os.remove(cname)
    else:
        open(cname, "w").write(host + "\n")
    print(f"built {len(pages)} pages + 404 for {BASE_URL}")

if __name__ == "__main__":
    build()
