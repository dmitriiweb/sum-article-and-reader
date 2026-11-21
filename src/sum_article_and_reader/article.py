def extract_article(url: str) -> tuple[str, str, str]:
    from newspaper import Article

    article = Article(url)
    article.download()
    article.parse()
    text = article.text.strip()
    if not text:
        raise ValueError("No article text found")
    return article.title.strip(), text, article.meta_lang.strip().lower()
