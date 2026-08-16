from core.jd_text import MAX_JD_CHARS, html_to_jd_text


def test_strips_script_style_nav_header_footer_aside():
    html = """
    <html><head><script>evil()</script><style>.a{}</style></head>
    <body>
    <nav>Home</nav><header>Header</header>
    <main><p>New grad Python engineer role.</p></main>
    <aside>Ads</aside><footer>Copyright</footer>
    </body></html>
    """
    text = html_to_jd_text(html)

    assert "New grad Python engineer role." in text
    for noise in ("evil()", "Home", "Header", "Ads", "Copyright"):
        assert noise not in text


def test_prefers_densest_main_block():
    html = """
    <body>
    <main>short</main>
    <article>A much longer job posting body with plenty of relevant detail.</article>
    </body>
    """
    text = html_to_jd_text(html)

    assert "much longer job posting" in text
    assert text != "short"


def test_falls_back_to_body_without_main_or_article():
    html = "<body><div>Backend Engineer role. Python and SQL required.</div></body>"

    assert "Backend Engineer role." in html_to_jd_text(html)


def test_collapses_whitespace():
    html = "<body><main>Role   with\n\nweird   spacing.</main></body>"

    assert html_to_jd_text(html) == "Role with weird spacing."


def test_caps_at_max_length():
    html = f"<body><main>{'word ' * 10_000}</main></body>"

    assert len(html_to_jd_text(html)) <= MAX_JD_CHARS


def test_prefers_json_ld_job_posting_over_js_only_shell():
    # a React/SPA shell: the only visible DOM text is a noscript notice, but
    # the real posting is embedded as schema.org JobPosting for SEO
    html = """
    <html><body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <script type="application/ld+json">
    {"@context": "https://schema.org/", "@type": "JobPosting",
     "title": "Backend Engineer",
     "description": "<p>We need a <b>Python</b> engineer with SQL experience.</p>"}
    </script>
    <div id="root"></div>
    </body></html>
    """
    text = html_to_jd_text(html)

    assert "Python" in text
    assert "enable JavaScript" not in text


def test_strips_related_jobs_carousel_and_nav_controls():
    # confirmed against a real careers page: a "Related Jobs" widget lives
    # as a sibling <section> inside <main>, not inside <footer>/<aside>, so
    # STRIP_TAGS' semantic-tag list alone doesn't catch it -- nor do nav
    # links/buttons like "Back to search results" and "Apply Now"
    html = """
    <body><main>
    <a href="/search">Back to search results</a>
    <button>Apply Now</button>
    <p>Backend Engineer role. Python and SQL required.</p>
    <section>
      <h2>Related Jobs</h2>
      <h3>Software Engineer, Data Engineering</h3>
      <p>San Mateo, CA, United States</p>
    </section>
    </main></body>
    """
    text = html_to_jd_text(html)

    assert "Backend Engineer role." in text
    for noise in ("Back to search results", "Apply Now", "Related Jobs", "Data Engineering"):
        assert noise not in text


def test_survives_deeply_nested_json_ld_instead_of_crashing():
    # json.loads recurses per nesting level -- deep-but-small nesting blows
    # Python's recursion limit and raises RecursionError, not a normal
    # ValueError/TypeError parse error, which used to crash the whole call
    nested = "[" * 20_000 + "]" * 20_000
    html = f"""
    <body>
    <script type="application/ld+json">{nested}</script>
    <p>Backend Engineer role. Python and SQL required for this position here.</p>
    </body>
    """
    text = html_to_jd_text(html)
    assert "Backend Engineer role." in text


def test_ignores_json_ld_when_dom_text_is_already_longer():
    html = """
    <body>
    <script type="application/ld+json">
    {"@type": "JobPosting", "description": "short"}
    </script>
    <main>A much longer, real job posting body with plenty of relevant detail.</main>
    </body>
    """
    assert "much longer" in html_to_jd_text(html)
