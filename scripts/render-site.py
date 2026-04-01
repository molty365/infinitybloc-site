#!/usr/bin/env python3
import json
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
site = json.loads((ROOT / 'content/site.json').read_text())
team = json.loads((ROOT / 'content/team.json').read_text())
bp = json.loads((ROOT / 'bp.json').read_text())
chains = json.loads((ROOT / 'chains.json').read_text())


def e(value):
    return escape(str(value), quote=True)


def render_links(items, cls=''):
    return '\n'.join(
        f'                <li><a href="{e(item["href"])}"{cls}>{e(item["label"])}</a></li>'
        for item in items
    )


def render_service_cards(items):
    out = []
    for item in items:
        out.append(f'''            <div class="service-card">
                <div class="service-icon"><i data-lucide="{e(item['icon'])}"></i></div>
                <h3>{e(item['title'])}</h3>
                <p>{e(item['description'])}</p>
            </div>''')
    return '\n'.join(out)


def render_expertise_items(items):
    return '\n'.join(
        f'                    <div class="expertise-item"><i data-lucide="{e(item["icon"])}" class="exp-icon"></i> {e(item["text"])}</div>'
        for item in items
    )


def render_tech_cards(items):
    return '\n'.join(
        f'''                <div class="tech-card">
                    <div class="icon"><i data-lucide="{e(item['icon'])}"></i></div>
                    <h4>{e(item['title'])}</h4>
                    <p>{e(item['description'])}</p>
                </div>'''
        for item in items
    )


def render_about_paragraphs(items):
    return '\n'.join(f'                <p>{e(text)}</p>' for text in items)


def render_about_links(items):
    out = []
    for i, item in enumerate(items):
        style = ' style="margin-right: 12px;"' if i == 0 and len(items) > 1 else ''
        out.append(
            f'                    <a href="{e(item["href"])}" target="_blank" class="btn btn-secondary"{style}>{e(item["label"])}</a>'
        )
    return '\n'.join(out)

homepage = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{e(site['site']['title'])}</title>
    <meta name="description" content="{e(site['site']['description'])}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{ --primary: #6366f1; --primary-dark: #4f46e5; --accent: #22d3ee; --accent-2: #a855f7; --bg-dark: #09090b; --bg-card: #18181b; --bg-card-hover: #27272a; --text: #fafafa; --text-muted: #a1a1aa; --border: rgba(255,255,255,0.08); --gradient-1: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #22d3ee 100%); --gradient-2: linear-gradient(135deg, #6366f1 0%, #22d3ee 100%); }}
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'Inter', -apple-system, sans-serif; background: var(--bg-dark); color: var(--text); line-height: 1.6; }}
        nav {{ position: fixed; top: 0; left: 0; right: 0; z-index: 100; padding: 16px 40px; display: flex; justify-content: space-between; align-items: center; background: rgba(9,9,11,0.8); backdrop-filter: blur(20px); border-bottom: 1px solid var(--border); }}
        .logo {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.4rem; font-weight: 700; color: var(--text); display: flex; align-items: center; gap: 10px; text-decoration: none; }}
        .logo-icon {{ width: 32px; height: 32px; background: var(--gradient-1); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1rem; }}
        .nav-links {{ display: flex; gap: 32px; list-style: none; }}
        .nav-links a {{ color: var(--text-muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; transition: color 0.2s; }}
        .nav-links a:hover {{ color: var(--text); }}
        .nav-cta {{ padding: 10px 20px; background: var(--text); border: none; border-radius: 8px; color: var(--bg-dark); font-weight: 600; font-size: 0.9rem; cursor: pointer; transition: all 0.2s; text-decoration: none; }}
        .nav-cta:hover {{ transform: translateY(-2px); box-shadow: 0 10px 30px rgba(255,255,255,0.1); }}
        .hero {{ min-height: 100vh; display: flex; align-items: center; padding: 120px 40px 80px; max-width: 1400px; margin: 0 auto; }}
        .hero-content {{ max-width: 700px; }}
        .hero-badge {{ display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.2); border-radius: 50px; font-size: 0.8rem; color: var(--accent); margin-bottom: 24px; }}
        .hero h1 {{ font-family: 'Space Grotesk', sans-serif; font-size: clamp(2.5rem, 6vw, 4rem); font-weight: 700; line-height: 1.1; margin-bottom: 24px; }}
        .hero h1 .gradient {{ background: var(--gradient-1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .hero p {{ font-size: 1.2rem; color: var(--text-muted); margin-bottom: 40px; line-height: 1.7; }}
        .hero-buttons {{ display: flex; gap: 16px; flex-wrap: wrap; }}
        .btn {{ padding: 14px 28px; border-radius: 10px; font-size: 0.95rem; font-weight: 600; cursor: pointer; transition: all 0.2s; text-decoration: none; display: inline-flex; align-items: center; gap: 8px; border: none; }}
        .btn-primary {{ background: var(--text); color: var(--bg-dark); }}
        .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 15px 40px rgba(255,255,255,0.15); }}
        .btn-secondary {{ background: transparent; color: var(--text); border: 1px solid var(--border); }}
        .btn-secondary:hover {{ background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.2); }}
        section {{ padding: 120px 40px; max-width: 1400px; margin: 0 auto; }}
        .section-label {{ font-size: 0.8rem; font-weight: 600; color: var(--accent); text-transform: uppercase; letter-spacing: 2px; margin-bottom: 12px; }}
        .section-title {{ font-family: 'Space Grotesk', sans-serif; font-size: clamp(2rem, 4vw, 3rem); font-weight: 700; margin-bottom: 16px; }}
        .section-desc {{ font-size: 1.1rem; color: var(--text-muted); max-width: 600px; margin-bottom: 60px; }}
        .services-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }}
        .service-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 32px; transition: all 0.3s; }}
        .service-card:hover {{ background: var(--bg-card-hover); border-color: rgba(99,102,241,0.3); transform: translateY(-4px); }}
        .service-icon {{ width: 48px; height: 48px; background: var(--gradient-2); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 20px; }}
        .service-icon svg {{ width: 24px; height: 24px; stroke: white; stroke-width: 2; }}
        .service-card h3 {{ font-size: 1.2rem; font-weight: 600; margin-bottom: 12px; }}
        .service-card p {{ color: var(--text-muted); font-size: 0.95rem; line-height: 1.6; }}
        .expertise-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 60px; align-items: center; }}
        .expertise-content h2, .about-content h2 {{ font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; margin-bottom: 20px; }}
        .expertise-content > p, .about-content p {{ color: var(--text-muted); font-size: 1.05rem; margin-bottom: 16px; line-height: 1.7; }}
        .expertise-list {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
        .expertise-item {{ display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: var(--bg-card); border-radius: 10px; font-size: 0.9rem; }}
        .expertise-item .exp-icon {{ width: 20px; height: 20px; stroke: var(--accent); stroke-width: 2; flex-shrink: 0; }}
        .expertise-visual {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
        .tech-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; text-align: center; transition: all 0.3s; }}
        .tech-card:hover {{ border-color: rgba(99,102,241,0.3); }}
        .tech-card .icon {{ margin-bottom: 12px; }}
        .tech-card .icon svg {{ width: 40px; height: 40px; stroke: var(--accent); stroke-width: 1.5; }}
        .tech-card h4 {{ font-size: 1rem; font-weight: 600; margin-bottom: 4px; }}
        .tech-card p {{ font-size: 0.8rem; color: var(--text-muted); }}
        .book-section {{ background: var(--bg-card); border-radius: 24px; padding: 80px; text-align: center; margin: 0 40px; max-width: calc(1400px - 80px); margin-left: auto; margin-right: auto; }}
        .book-section h2 {{ font-family: 'Space Grotesk', sans-serif; font-size: clamp(2rem, 4vw, 2.5rem); margin-bottom: 16px; }}
        .book-section > p {{ color: var(--text-muted); font-size: 1.1rem; max-width: 500px; margin: 0 auto 40px; }}
        .calendly-wrapper {{ background: var(--bg-dark); border-radius: 16px; padding: 20px; max-width: 700px; margin: 0 auto; }}
        .calendly-inline-widget {{ min-height: 650px; border-radius: 12px; overflow: hidden; }}
        .book-fallback {{ padding: 60px 40px; border: 2px dashed var(--border); border-radius: 12px; }}
        .book-fallback p {{ color: var(--text-muted); margin-bottom: 24px; }}
        .about-grid {{ display: grid; grid-template-columns: 1fr 2fr; gap: 60px; align-items: center; }}
        .about-image {{ width: 100%; max-width: 350px; aspect-ratio: 1; border-radius: 20px; overflow: hidden; background: var(--gradient-1); }}
        .about-image img {{ width: 100%; height: 100%; object-fit: cover; }}
        .about-content p strong {{ color: var(--text); }}
        footer {{ padding: 60px 40px 30px; border-top: 1px solid var(--border); margin-top: 80px; }}
        .footer-content {{ max-width: 1400px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px; }}
        .footer-links {{ display: flex; gap: 32px; list-style: none; }}
        .footer-links a {{ color: var(--text-muted); text-decoration: none; font-size: 0.9rem; transition: color 0.2s; }}
        .footer-links a:hover {{ color: var(--text); }}
        .footer-bottom {{ max-width: 1400px; margin: 40px auto 0; padding-top: 20px; border-top: 1px solid var(--border); text-align: center; color: var(--text-muted); font-size: 0.85rem; }}
        @media (max-width: 1024px) {{ .services-grid {{ grid-template-columns: 1fr 1fr; }} .expertise-grid, .about-grid {{ grid-template-columns: 1fr; }} .about-image {{ max-width: 300px; margin: 0 auto; }} }}
        @media (max-width: 768px) {{ nav {{ padding: 12px 20px; }} .nav-links {{ display: none; }} .hero {{ padding: 100px 20px 60px; }} section {{ padding: 80px 20px; }} .services-grid, .expertise-list {{ grid-template-columns: 1fr; }} .expertise-visual {{ grid-template-columns: 1fr 1fr; }} .book-section {{ padding: 40px 20px; margin: 0 20px; }} .footer-content {{ flex-direction: column; text-align: center; }} .mobile-menu-btn {{ display: block; }} }}
        .mobile-menu-btn {{ display: none; background: none; border: none; color: white; font-size: 1.5rem; cursor: pointer; }}
    </style>
</head>
<body>
    <nav>
        <a href="#" class="logo">
            <div class="logo-icon">{e(site['site']['logoSymbol'])}</div>
            {e(site['site']['brandName'])}
        </a>
        <ul class="nav-links">
{render_links(site['navigation']['links'])}
        </ul>
        <a href="{e(site['navigation']['cta']['href'])}" class="nav-cta">{e(site['navigation']['cta']['label'])}</a>
        <button class="mobile-menu-btn">☰</button>
    </nav>

    <section class="hero">
        <div class="hero-content">
            <div class="hero-badge">{e(site['hero']['badge'])}</div>
            <h1>{e(site['hero']['titlePrefix'])}<span class="gradient">{e(site['hero']['titleHighlight'])}</span></h1>
            <p>{e(site['hero']['description'])}</p>
            <div class="hero-buttons">
                <a href="{e(site['hero']['primaryButton']['href'])}" class="btn btn-primary">{e(site['hero']['primaryButton']['label'])}</a>
                <a href="{e(site['hero']['secondaryButton']['href'])}" class="btn btn-secondary">{e(site['hero']['secondaryButton']['label'])}</a>
            </div>
        </div>
    </section>

    <section id="services">
        <span class="section-label">{e(site['services']['label'])}</span>
        <h2 class="section-title">{e(site['services']['title'])}</h2>
        <p class="section-desc">{e(site['services']['description'])}</p>
        <div class="services-grid">
{render_service_cards(site['services']['items'])}
        </div>
    </section>

    <section id="expertise">
        <div class="expertise-grid">
            <div class="expertise-content">
                <span class="section-label">{e(site['expertise']['label'])}</span>
                <h2>{e(site['expertise']['title'])}</h2>
                <p>{e(site['expertise']['description'])}</p>
                <div class="expertise-list">
{render_expertise_items(site['expertise']['items'])}
                </div>
            </div>
            <div class="expertise-visual">
{render_tech_cards(site['expertise']['techCards'])}
            </div>
        </div>
    </section>

    <div class="book-section" id="book">
        <span class="section-label">{e(site['book']['label'])}</span>
        <h2>{e(site['book']['title'])}</h2>
        <p>{e(site['book']['description'])}</p>
        <div class="calendly-wrapper">
            <div class="calendly-inline-widget" data-url="{e(site['book']['calendlyUrl'])}" style="min-width:320px;height:700px;"></div>
            <script type="text/javascript" src="https://assets.calendly.com/assets/external/widget.js" async></script>
            <noscript>
                <div class="book-fallback">
                    <p>Book a meeting directly:</p>
                    <a href="{e(site['book']['fallbackUrl'])}" class="btn btn-primary" target="_blank">{e(site['book']['fallbackLabel'])}</a>
                </div>
            </noscript>
        </div>
    </div>

    <section id="about">
        <div class="about-grid">
            <div class="about-image"><img src="{e(site['about']['image'])}" alt="{e(site['about']['imageAlt'])}"></div>
            <div class="about-content">
                <span class="section-label">{e(site['about']['label'])}</span>
                <h2>{e(site['about']['name'])}</h2>
                <p><strong>{e(site['about']['role'])}</strong></p>
{render_about_paragraphs(site['about']['paragraphs'])}
                <div style="margin-top: 24px;">
{render_about_links(site['about']['links'])}
                </div>
            </div>
        </div>
    </section>

    <footer>
        <div class="footer-content">
            <a href="#" class="logo">
                <div class="logo-icon">{e(site['site']['logoSymbol'])}</div>
                {e(site['site']['brandName'])}
            </a>
            <ul class="footer-links">
{render_links(site['footer']['links'])}
            </ul>
        </div>
        <div class="footer-bottom">
            <p>{e(site['footer']['copyright'])}</p>
        </div>
    </footer>
    <script>lucide.createIcons();</script>
</body>
</html>
'''

team_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Team - Infinitybloc</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 20px; line-height: 1.6; }}
        h1 {{ color: #1a1a2e; }}
    </style>
</head>
<body>
    <h1>{e(team['title'])}</h1>
    <p>{e(team['intro'])}</p>

    <h2>{e(team['missionTitle'])}</h2>
    <p>{e(team['mission'])}</p>

    <h2>{e(team['leadershipTitle'])}</h2>
    <p><strong>{e(team['leaderName'])}</strong> - {e(team['leaderRole'])}</p>
    <p>{e(team['leaderBio'])}</p>

    <h2>{e(team['ownershipTitle'])}</h2>
    <p>{e(team['ownership'])}</p>

    <p>Contact: {e(team['contactEmail'])}</p>
    <p>Last updated: {e(team['lastUpdated'])}</p>
</body>
</html>
'''

(ROOT / 'index.html').write_text(homepage)
(ROOT / 'team.html').write_text(team_html)
print('Rendered index.html and team.html from content JSON')
