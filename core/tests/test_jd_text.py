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
