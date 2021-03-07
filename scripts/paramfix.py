"""Fix dublicate params in templates."""
import pywikibot
import mwparserfromhell

CATEGORY = "Категория:Страницы, использующие повторяющиеся аргументы в вызовах шаблонов"
COMMENT = "Исправление повторяющихся параметров в шаблонах."

def fix_page(page):
    """Fix dublicate params at single page."""
    text = page.text
    code = mwparserfromhell.parse(text)
    fixed = False
    for template in code.filter_templates():
        data = {}
        to_delete = []
        params = template.params
        idx = 0
        while idx < len(params):
            current = params[idx]
            name = current.name.strip()
            if name not in data:
                data[name] = [current]
                idx += 1
                continue
            if current.value.strip() == "":
                # empty dublicate, delete it
                template.remove(current)
                fixed = True
                continue
            previous = data[name][0]
            if len(data[name]) == 1 and previous.value.strip() == "":
                # before was an empty param with the same name, delete it
                template.remove(previous)
                fixed = True
                data[name] = [current]
                continue
            for previous in data[name]:
                if previous.value.strip() == current.value.strip():
                    # there are two equal parameters, delete the second one
                    template.remove(current)
                    fixed = True
                    current = None
                    break
            if current is not None:
                data[name].append(current)
                idx += 1
    if fixed:
        try:
            page.text = text
            page.save(COMMENT)
        except pywikibot.exceptions.Error:
            pass

def main():
    """Main script function."""
    site = pywikibot.Site()
    category = pywikibot.Category(site, CATEGORY)
    for page in category.members(namespaces=["0"]):
        fix_page(page)

if __name__ == "__main__":
    main()
