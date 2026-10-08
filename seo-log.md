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

Redesign + legal 14:30 BST: light cute redesign and Terms, Disclaimer, Privacy (LLC, Michigan law) live, all 200. IndexNow 24 URLs: HTTP 200.
