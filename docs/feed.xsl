<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/MathML" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/">
    <html lang="en">
      <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title><xsl:value-of select="rss/channel/title"/> — RSS Feed</title>
        <style>
          :root {
            --bg: #0d1117;
            --card-bg: #161b22;
            --text: #e6edf3;
            --text-muted: #8b949e;
            --accent: #2dd9e0;
            --border: #30363d;
            --purple: #7b61ff;
          }
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 2rem 1rem;
            line-height: 1.6;
          }
          .container {
            max-width: 800px;
            margin: 0 auto;
          }
          .header-banner {
            background: linear-gradient(135deg, rgba(45, 217, 224, 0.15), rgba(123, 97, 255, 0.15));
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
          }
          h1 {
            margin: 0 0 0.5rem 0;
            font-size: 1.75rem;
            color: var(--text);
          }
          p.desc {
            color: var(--text-muted);
            margin: 0 0 1rem 0;
            font-size: 0.95rem;
          }
          .hint-box {
            background: rgba(255, 255, 255, 0.05);
            border-left: 4px solid var(--accent);
            padding: 0.75rem 1rem;
            font-size: 0.85rem;
            border-radius: 4px;
          }
          .article-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1.25rem;
            margin-bottom: 1.25rem;
            transition: transform 0.2s, border-color 0.2s;
          }
          .article-card:hover {
            border-color: var(--accent);
          }
          .article-title {
            font-size: 1.2rem;
            margin: 0 0 0.5rem 0;
          }
          .article-title a {
            color: var(--accent);
            text-decoration: none;
          }
          .article-title a:hover {
            text-decoration: underline;
          }
          .pub-date {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-bottom: 0.75rem;
          }
          .summary {
            font-size: 0.9rem;
            color: var(--text-muted);
            margin: 0;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header-banner">
            <h1>📡 Protodex RSS Feed</h1>
            <p class="desc">Real-time dataset releases, prediction market analytics, and AI agent intelligence.</p>
            <div class="hint-box">
              💡 <strong>RSS Feed Active:</strong> You can copy this page URL (<code>https://protodex.io/feed.xml</code>) directly into Feedly, NewsBlur, NetNewsWire, or any RSS reader to subscribe automatically.
            </div>
          </div>

          <div class="articles-list">
            <xsl:for-each select="rss/channel/item">
              <div class="article-card">
                <h2 class="article-title">
                  <a href="{link}" target="_blank"><xsl:value-of select="title"/></a>
                </h2>
                <div class="pub-date">Published: <xsl:value-of select="pubDate"/></div>
                <p class="summary"><xsl:value-of select="description"/></p>
              </div>
            </xsl:for-each>
          </div>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
