# PandasWise SEO log

## 2026-10-08 Day 1 launch (no Search Console data yet)
Built v1: 21 indexable pages (home, 9 guides, where-to-see-pandas tool, 6 blog posts, blog index, about, contact, privacy) plus 404.
Pick for unique asset: where-to-see-pandas.html, because "where to see pandas / which zoos have pandas" results go stale fast
(Wikipedia was wrong for Malaysia, Belgium and France on launch day) and a dated, per row sourced table is genuinely more useful.

Flagship upgrade (11:42 steering): every row on where-to-see-pandas now links the zoo's own official page (or operator or government page) with "Last verified 8 Oct 2026"; 21 giant panda zoos, 2 China places, 6 red panda zoos. Nav item 2 and a featured home card.
Rebrand (11:55 steering): PandasWise, repo renamed to pandaswise, base URL https://joshuaofisrael.github.io/pandaswise/.
Live check 11:58 BST: all 22 sitemap URLs plus robots.txt, sitemap.xml, llms.txt, key file, og.png and style.css return 200; 404 page returns 404; GPTBot, ClaudeBot, PerplexityBot, Googlebot and Bingbot user agents get 200.
IndexNow 11:58 BST: POST api.indexnow.org with all 22 sitemap URLs (includes blog/why-are-red-pandas-red.html), host joshuaofisrael.github.io, keyLocation /pandaswise/3307b908c0c7e41a8ba7f9140b4756d5.txt: HTTP 202 (accepted, key validation pending).

Domain switch 12:27 to 12:38 BST: pandaswise.com live with HTTPS enforced (cert for apex and www). All 22 sitemap URLs return 200 on https://pandaswise.com/; www, http and the old github.io URL all 301 to https://pandaswise.com/.
IndexNow 12:38 BST: host pandaswise.com, 22 URLs, keyLocation https://pandaswise.com/3307b908c0c7e41a8ba7f9140b4756d5.txt: HTTP 202.
FormSubmit 12:28 BST: one activation test POST from pandaswise.com origin: HTTP 200, activation email sent.

## Scorecard
| Date | Window | Impressions | Clicks | CTR | Avg pos | Indexed pages | Top100/20/10/3 queries | Growing pages | Declining pages | Conversions |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-08 | 7d | n/a (no GSC yet) | n/a | n/a | n/a | 22 URLs in sitemap (pandaswise.com) | n/a | n/a | n/a | n/a |

Redesign + legal 14:30 BST: light cute redesign and Terms, Disclaimer, Privacy (LLC, governing law) live, all 200. IndexNow 24 URLs: HTTP 200.
LLC Florida fix 14:3x BST: Terms governing law and venue now Florida; llms.txt updated.
- 2026-10-11 00:3x: games hub launched (3 new URLs); IndexNow pinged.
- 2026-10-12 00:37: Published daily fact article /blog/do-pandas-have-thumbs.html (FAQPage JSON-LD, 3 verified DOIs, internal links); IndexNow HTTP 200 for article, blog index, sitemap. Next slot: Cite this page box plus last reviewed dates (EDU step 1).
- 2026-10-13 00:3x: Published daily fact article /blog/how-big-is-a-red-panda-home-range.html (FAQPage JSON-LD, 3 verified DOIs: 10.3354/esr01171, 10.1007/s10980-021-01357-w, 10.1371/journal.pone.0180978; IndexNow HTTP 200). Also shipped Cite this page (APA/MLA/Chicago) and Last reviewed on pillars and posts; LearningResource JSON-LD on /teachers/. Next: PDF printables.
- 13 Oct 2026 09:34 BST: IndexNow HTTP 200 for /teachers/ and 3 new printable PDFs.
- 2026-10-14 09:37 London: published daily fact /blog/why-are-baby-pandas-so-small.html (09:25 slot, 00:25 slot had failed); IndexNow HTTP 200 for article, blog index, sitemap.
- 2026-10-15 00:3x London: published daily fact /blog/how-do-red-pandas-stay-warm.html (FAQPage JSON-LD, DOIs 10.1371/journal.pone.0173274 and 10.1086/physzool.61.3.30161241 verified on Crossref, plus Smithsonian and Nie 2015); IndexNow HTTP 200 for article, blog index, sitemap. Drafted educator outreach plan and template at drafts/OUTREACH-PLAN.md (nothing sent); next: build verified research/outreach-targets.csv, then send plan to Personal assistant for Joshua's yes.
- 2026-10-16 00:3x London: published daily fact /blog/how-long-is-a-giant-panda-pregnancy.html (FAQPage JSON-LD; DOIs 10.1530/rep-09-0241, 10.1016/j.therwi.2023.100063, 10.1038/s41598-025-19067-7, 10.3390/ani15081182 verified on Crossref, plus Smithsonian); IndexNow HTTP 200 for article, blog index, sitemap (live URL verified after Pages rebuild; first Pages build errored then rebuilt OK). EDU extras skipped for time (hard stop 00:45). Cloudflare beacon still skipped.
