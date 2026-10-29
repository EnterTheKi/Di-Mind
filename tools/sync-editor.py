"""Regenerate edit-book.html from the template with the current book source embedded."""
import io
import re

tpl = io.open('book-source/edit-book.template.html', encoding='utf-8').read()
md = io.open('book-source/the-switch.md', encoding='utf-8').read()
js_safe = md.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
new = re.sub(
    r"(<!--BEGIN_BOOK_SOURCE-->)[\s\S]*?(<!--END_BOOK_SOURCE-->)",
    lambda m: m.group(1) + "\n" + js_safe + "\n" + m.group(2),
    tpl,
    count=1,
)
io.open('edit-book.html', 'w', encoding='utf-8', newline='\n').write(new)
print('edit-book.html regenerated,', len(new), 'bytes')
