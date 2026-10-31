# LUMEN website — 26 October 2026

Reference: user-provided website mockup and imagery. Warm white, champagne gold, black serif headings; Marina Bay photographic hero, compact editorial sections, a restrained world map.

`build_site.py` is the canonical content and locale generator. `python build_site.py` generates the simplified Chinese, traditional Chinese and English pages. `translate.py` delegates to it. Shared runtime and styles live in `dist/app.js` and `dist/styles.css`. Source snapshots live under `source/`.

Photos and map are supplied user assets, compressed as WebP. `lumen-horizontal.png` repositions the original supplied emblem and original lettering without redrawing or stretching. `lumen-logo.svg` retains the original complete square logo.

CMS fund management status checked against the MAS directory on 26 October 2026 (record 412830, not a licence number). US$800M+ describes the team’s historical experience, not firm AUM. Map markers represent perspective, not confirmed offices. Contact form prepares a local email draft for the visitor to review and send; no submissions are collected or automatically sent.

Existing public Sites project and slug retained. lumstrat.com DNS is untouched. Simulator is a separate project and is unchanged.

QA: browser desktop rendering, 375px effective mobile frame layout without horizontal scrolling, mobile menu open/close and contact anchor, strategy tab change, product modal, simplified/traditional/English language navigation; local assets and fragment identifiers checked for all locales. Mail app delivery is user-controlled and not tested.

Latest requested revision: removed the hero-adjacent credential strip; retained lower CMS / team experience / Multi-Strategy cards. Added user-supplied licence number No. 101945 (not independently verified by the directory). Expanded the world view and removed its caption as requested. Public-market tabs now show the three supplied strategies: MEV arbitrage, quantitative futures hedging and market value management; all locale copy updated. Three-tab pointer/keyboard handling updated. Desktop and 375px effective mobile browser layout checked.

Homepage carousel: paired full-slide image and copy, 10-second default interval, previous/next, indicators, pause/play, hover/focus/hidden-tab pause and reduced-motion support. Supplied Marina Bay Sands photo used for an explicitly indicative investment-dialogue theme, with no invented event date or venue. Middle principle renamed to 严格风控 across locales. Browser verified automatic transition and mobile first/event layouts.

Carousel controls reduced to two 7px translucent circles with invisible 26x44 touch targets. Large background, arrows and counter hidden; extra controls remain keyboard-accessible on focus. Ten-second rotation unchanged.

Section order updated: hero → about → global map → core business → partner eligibility → contact. All three locales checked.

Partnership criteria redesigned from the five supplied mockups: five original photos are paired with the five existing criteria, using large editorial typography, warm translucent gradients, bilingual captions, page count and manual previous/next navigation. Touch swipe and keyboard arrow navigation provided. No automatic rotation added to this reading-focused section. All five image/title/page pairings browser checked, plus mobile layout at 375px with no horizontal overflow.

Latest edits: full company name in why-choose heading; product modal replaced verbatim with user-provided 50:50 product summary and risk text, prior term paragraph removed from that modal. Partnership showcase now automatically advances every 10 seconds while visible, pauses on hover/focus/hidden tab or reduced-motion preference, and uses five small translucent dots. Former arrows and pause remain available on keyboard focus; visible footer page counter hidden. Desktop automatic progression and mobile dot click/overflow checked.

Partnership photography now spans the full viewport, with section heading and copy aligned to the existing content grid. Shared across all locales; autoplay and dots retained.

Partnership slide 5 uses user supplied IMG_2248.jpeg, replacing the previous photograph.

Contact address no longer includes Suite 2018. Form now posts to a server endpoint with durable D1 storage; success dialog only opens after confirmed persistence. No email provider is configured.

English is the default root homepage. Simplified Chinese is at /zh-hans/. Traditional Chinese is removed from both navigation and routing.
