# Карта проекта для чеклистёра

## Приложение

ThreadQA XPath Practice Hub — публичный учебный тренажёр XPath/CSS для Selenium.
Хаб: https://lms.threadqa.ru/xpath-practice-hub

- Без регистрации и авторизации — предусловия кейсов обычно «открыта страница X».
- Arrange через API и cleanup аккаунтов не нужны.
- Страницы практики — естественные функциональные блоки чеклиста.
- Theory / Reference / игра XPath Diner — справочный и игровой контент: в скоуп
  функциональных проверок не входит, если человек явно не включит.

## Страницы практики

URL: `https://lms.threadqa.ru/xpath-practice-hub/practice/<slug>`
Замер DOM выполнен 2026-10-06 в браузере.

| Страница | data-testid | Замечания по локаторам |
|---|---|---|
| basic-elements | 20 | инпуты, выпадающий список, чекбоксы, кнопки, алерты, модалка, тосты, ссылки |
| interactive-elements | 9 | |
| multi-step-form | 22 | |
| autocomplete | 1 | почти без тестидов — локаторы `id`/`name`/`aria-label` |
| calendar | 10 | |
| context-menu | 1 | почти без тестидов — локаторы `id`/`name`/`aria-label` |
| data-table | 47 | |
| ecommerce | 32 | |
| blog-posts | 45 | |
| products | 39 | |
| accordion | 32 | |
| media-controls | 6 | |
| system-status | 6 | |
| complex-selectors | 14 | |
| pseudo-classes | 7 | |
| shadow-dom-iframe | 4 (+3 внутри shadow root) | 2 iframe, 2 shadow root; XPath внутрь shadow DOM не работает |

Примеры тестидов с basic-elements: `username-field`, `email-field`, `password-field`,
`comment-field`, `country-dropdown`, `terms-agreement`, `newsletter-yes`, `primary-button`,
`show-alert-button`, `open-modal-button`, `notify-success`, `external-link`.

Названия страниц говорят сами за себя, но что именно лежит на странице — осмотри
реальный DOM в браузере перед дизайном блока. Не проектируй проверки по названию slug.

## Как читать страницу

1. Открой `.../practice/<slug>` в браузере (ZCode browser-use).
2. Возьми DOM-снимок: роли, доступные имена, состояния элементов.
3. Проверь фактические `data-testid`, `id`, `aria-label` — только они идут в кейсы
   как основа будущих локаторов (сам локатор соберёт ai-avtomatizator).

## Грабли (проверено на живом стенде)

- Тестид — приоритет, но не гарантия: на autocomplete и context-menu их почти нет.
- Shadow DOM: XPath внутрь не работает — ни на этом стенде, ни в Selenium вообще.
- Из части окружений сайт недоступен напрямую (curl/SSL-ошибка), при этом в браузере
  открывается нормально — проверяй стенд через браузер, а не через HTTP-запросы.
