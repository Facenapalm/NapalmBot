"""Add missing references section to pages with refs, comes from wikidata."""

import pywikibot
import checkwiki

CATEGORY = "Категория:Википедия:Статьи с источниками из Викиданных"
TEMPLATE = "Шаблон:Примечания"
COMMENT = "Исправление отсутствующей секции примечаний."

def main():
    """Main script function."""
    site = pywikibot.Site()
    category = pywikibot.Category(site, CATEGORY)
    refs = [page.title() for page in category.articles(namespaces=[0])]
    template = pywikibot.Page(site, TEMPLATE)
    references = set([page.title() for page in template.embeddedin(namespaces=[0])])
    pages = [pywikibot.Page(site, page) for page in refs if not page in references]
    # converting to titles and back is needed for saving memory
    for page in pages:
        (text, flag) = checkwiki.insert_references(page.text)
        if flag:
            (text, fixes) = checkwiki.process_text(text)
            page.text = text
            page.save(COMMENT)
            checkwiki.mark_error_list_done(fixes, page.title())

if __name__ == "__main__":
    main()
