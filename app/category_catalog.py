# -*- coding: utf-8 -*-
"""分類列表頁資料：/browse/<section>/<slug>"""

SECTION_LABELS = {
    'maternity': '母嬰',
    'personal': '個人護理、健康',
    'home': '家居生活',
    'pet': '寵物區',
}

ALLOWED = {
    'maternity': frozenset({'formula', 'diaper', 'food', 'care', 'gear', 'prenatal'}),
    'personal': frozenset({
        'oral', 'body', 'hair', 'handfoot', 'women', 'skin', 'shave',
        'intimate', 'adultcare', 'pharma', 'health',
    }),
    'home': frozenset({
        'tissue', 'homeclean', 'kitchenclean', 'bathroomclean', 'laundry',
        'kitchenware', 'appliance', 'decor', 'travelgarden', 'homecare',
    }),
    'pet': frozenset({'cat', 'dog', 'other', 'clean', 'food', 'supplies'}),
}

SLUG_TITLES = {
    ('maternity', 'formula'): '嬰幼兒奶粉',
    ('maternity', 'diaper'): '紙尿片',
    ('maternity', 'food'): '嬰幼兒食品',
    ('maternity', 'care'): '嬰幼兒護理',
    ('maternity', 'gear'): '嬰幼兒用品',
    ('maternity', 'prenatal'): '孕婦／產前產後',
    ('personal', 'oral'): '口腔護理',
    ('personal', 'body'): '身體護理',
    ('personal', 'hair'): '頭髮護理',
    ('personal', 'handfoot'): '手、腳部護理',
    ('personal', 'women'): '女士衛生護理',
    ('personal', 'skin'): '護膚美妝',
    ('personal', 'shave'): '男士剃鬚用品',
    ('personal', 'intimate'): '安全套、成人情趣用品',
    ('personal', 'adultcare'): '成人護理用品',
    ('personal', 'pharma'): '醫藥產品',
    ('personal', 'health'): '保健產品',
    ('home', 'tissue'): '紙巾、廁紙',
    ('home', 'homeclean'): '家居清潔',
    ('home', 'kitchenclean'): '廚房清潔',
    ('home', 'bathroomclean'): '浴室清潔',
    ('home', 'laundry'): '洗衣',
    ('home', 'kitchenware'): '廚房用品與餐具',
    ('home', 'appliance'): '家用電器與影音設備',
    ('home', 'decor'): '家居用品、佈置',
    ('home', 'travelgarden'): '旅行及園藝用品',
    ('home', 'homecare'): '家居護理',
    ('pet', 'cat'): '貓用品',
    ('pet', 'dog'): '狗用品',
    ('pet', 'other'): '其他寵物用品',
    ('pet', 'clean'): '寵物家居清潔',
    ('pet', 'food'): '寵物食品',
    ('pet', 'supplies'): '寵物用品',
}

DEFAULT_DESC = '網上選購優質商品，享送貨或店取服務。'


def _sample_products(diaper_style=True, n=12):
    names = [
        'Huggies 親然紙尿片 L 40片',
        'Merries 花王紙尿片 M 64片',
        'Pampers Ichiban 黏貼型 S 84片',
        'GOO.N 大王紙尿片 NB 90片',
        'Moony 尤妮佳學習褲 XL 38片',
        'HUGGIES 夜安褲 L-XL 12片',
    ]
    out = []
    for i in range(n):
        nm = names[i % len(names)]
        if not diaper_style:
            nm = nm.replace('紙尿片', '商品').replace('學習褲', '精選') + f' #{i + 1}'
        elif i >= len(names):
            nm = f'{nm} · 組合 {i + 1}'
        rating = 4.0 + (i % 3) * 0.5
        stars_full = min(5, int(round(rating)))
        out.append({
            'name': nm,
            'unit': '1 PACK',
            'rating': rating,
            'stars_full': stars_full,
            'reviews': 32 + i * 17,
            'price': 89.0 + (i % 5) * 11 + i * 0.5,
            'img_mod': (i % 8) + 1,
        })
    return out


def _diaper_subcats():
    sizes = [
        ('初生 NB', 15),
        ('細碼 S', 22),
        ('中碼 M', 28),
        ('大碼 L', 31),
        ('加大碼 XL', 18),
        ('加加大碼 XXL', 9),
        ('學習褲', 24),
    ]
    return [
        {'label': a, 'count': b, 'slug': f'sz-{i}', 'img_mod': (i % 8) + 1}
        for i, (a, b) in enumerate(sizes)
    ]


def build_browse_page(section, slug):
    if section not in ALLOWED or slug not in ALLOWED[section]:
        return None

    title = SLUG_TITLES.get((section, slug), slug)
    desc = DEFAULT_DESC
    if (section, slug) == ('maternity', 'diaper'):
        desc = '紙尿片、學習褲及夜用褲等，照顧寶寶每個成長階段。'

    breadcrumbs = [
        {'label': '首頁', 'url': '/'},
        {'label': SECTION_LABELS[section], 'url': None},
        {'label': title, 'url': None},
    ]

    subcategories = []
    products = _sample_products(diaper_style=(slug == 'diaper'), n=12)

    if (section, slug) == ('maternity', 'diaper'):
        subcategories = _diaper_subcats()
    elif section == 'maternity' and slug == 'formula':
        subcategories = [
            {'label': f'第{i}階段', 'count': 8 + i * 3, 'slug': f'stage-{i}', 'img_mod': i}
            for i in range(1, 6)
        ]
        subcategories.append({'label': '特別配方', 'count': 12, 'slug': 'special', 'img_mod': 6})
    else:
        subcategories = [
            {'label': '熱門精選', 'count': 20, 'slug': 'hot', 'img_mod': 1},
            {'label': '新品', 'count': 8, 'slug': 'new', 'img_mod': 2},
            {'label': '套裝優惠', 'count': 6, 'slug': 'bundle', 'img_mod': 3},
            {'label': '原箱', 'count': 4, 'slug': 'case', 'img_mod': 4},
        ]

    filter_tabs = [
        {'id': 'class', 'label': '分類', 'active': True},
        {'id': 'brand', 'label': '品牌', 'active': False},
        {'id': 'price', 'label': '價格', 'active': False},
        {'id': 'sort', 'label': '排序', 'active': False},
        {'id': 'origin', 'label': '產地', 'active': False},
    ]

    sort_options = [
        {'id': 'popular', 'label': '熱門', 'active': True},
        {'id': 'new', 'label': '最新', 'active': False},
        {'id': 'rating', 'label': '評分', 'active': False},
        {'id': 'price_asc', 'label': '價格（低至高）', 'active': False},
        {'id': 'price_desc', 'label': '價格（高至低）', 'active': False},
    ]

    return {
        'title': f'{title} - PNS',
        'browse_title': title,
        'browse_description': desc,
        'breadcrumbs': breadcrumbs,
        'subcategories': subcategories,
        'products': products,
        'filter_tabs': filter_tabs,
        'sort_options': sort_options,
        'browse_section': section,
        'browse_slug': slug,
    }
