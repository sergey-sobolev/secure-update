# Отчёт о выполнении задачи "Secure update"

- [Отчёт о выполнении задачи "Secure update"](#отчёт-о-выполнении-задачи-secure-update)
  - [Постановка задачи](#постановка-задачи)
  - [Известные ограничения и вводные](#известные-ограничения-и-вводные)
    - [Цели и Предположения Безопасности (ЦПБ)](#цели-и-предположения-безопасности-цпб)
  - [Архитектура системы](#архитектура-системы)
    - [Компоненты](#компоненты)
      - [Монитор безопасности (security monitor)](#монитор-безопасности-security-monitor)
    - [Алгоритм работы решения](#алгоритм-работы-решения)
    - [Описание Сценариев (последовательности выполнения операций), при которых ЦБ нарушаются](#описание-сценариев-последовательности-выполнения-операций-при-которых-цб-нарушаются)
    - [Указание "доверенных компонент" на архитектурной диаграмме с обоснованием выбора.](#указание-доверенных-компонент-на-архитектурной-диаграмме-с-обоснованием-выбора)
    - [Политики безопасности](#политики-безопасности)
  - [Запуск приложения и тестов](#запуск-приложения-и-тестов)
    - [Запуск приложения](#запуск-приложения)
    - [Запуск тестов](#запуск-тестов)

## Постановка задачи

Задача заключается в обновлении приложения (может быть прошивкой устройства), при условии, что файл обновления авторизован - то есть соответствует версии файла, полученной из доверенного источника (от поставщика прошивки).

## Известные ограничения и вводные

По условиям организаторов должна использоваться микросервисная архитектура и шина обмена сообщениями для реализации асинхронной работы сервисов.

### Цели и Предположения Безопасности (ЦПБ)

- Целью безопасности в нашем случае будет обеспечение возможности применения только правильных обновлений.
В данном случае правильный – это некий набор проверок, который мы определили как достаточный.

- Далее, для простоты примера, мы сразу же оставим за скобками проблемы доставки обновления на устройство и возможные атаки на доставку. И наконец, мы не будем рассматривать вопросы физической безопасности устройства.

## Архитектура системы

### Компоненты

- **Downloader** скачивает данные из сетей общего пользования
- **Manager** оркестрирует весь процесс обновления
- **Verifier** проверят корректность скачанной прошивки
- **Storage** осуществляет хранение скачанной прошивки
- **Updater** непосредственно применяет обновление
- **Security monitor** (монитор безопасности) авторизует операцию, если она удовлетворяет заданным правилам или блокирует её в противном случае

![HLA](./diagrams/docs/report/hla/hla.png?raw=true "Архитектура")

#### Монитор безопасности (security monitor)

На логическом уровне коммуникация выглядит так

![SM](./diagrams/docs/report/sm/sm.png?raw=true "Монитор безопасности")

Т.е. менеджер обновлений поручает сервису verifier проверить обновление, которое тот берёт у сервиса storage, а монитор безопасности проверяет, что вся эта цепочка операций была проделана, и только в этом случае разрешает обратиться к сервису обновления.

### Алгоритм работы решения

![Sequence diagram](./diagrams/docs/report/sd/sd.png?raw=true "Диаграмма вызовов")

### Описание Сценариев (последовательности выполнения операций), при которых ЦБ нарушаются

Давайте посмотрим на процесс обновления с точки зрения безопасности, чтобы найти потенциальные проблемы, то есть сценарии, где возможна компрометации целей безопасности.

Наши вводные, исходя из выбранного охвата задач: на устройство доставлена прошивка и теперь нам надо устройство обновить.

Первая значимая команда в диаграмме – это запрос на проверку и первая возможная проблема, компонент Manager «забыл» отправить запрос на проверку, и таким образом в результате на обновление отправится непроверенная версия.

Следующая значимая команда – запрос на обновление и следующая возможная проблема, это то, что результат проверки может быть проигнорирован и запрос на обновление может отправиться неверная версия прошивки.

Следующая возможная проблема уже не связана командами, но она отражает тот факт, что между тем, как обновление проверено и запросом на обновление от Manager есть некий зазор по времени. В этот период времени данные обновления могут быть изменены, и на обновление может отправиться неверная версия прошивки.

Детальный анализ может выявить ещё и другие проблемы, например, роллбэк атаку и т.д., но для понимания механизмов будет достаточно и самых очевидных. Поэтому, для упрощения политик безопасности примера мы будем рассматривать следующие три очевидных сценария:

* «забыли» отправить запрос на проверку обновления;
* результат проверки проигнорировали;
* данные обновления изменили после проверки.
  
Ниже представлены три выбранные сценария компрометации целей безопасности на диаграмме процесса обновления:

![Негативные сценарии](./diagrams/docs/report/sd-negative/sd-negative.png?raw=true "Негативные сценарии")


### Указание "доверенных компонент" на архитектурной диаграмме с обоснованием выбора.

В общем случае, компонент Manager может быть недоверенным, результаты проверки могут быть игнорированы или данные могут изменены после проверки.

Так как шина обмена сообщений и монитор безопасности являются общесистемными, они в данной системе выбраны доверенными (а это значит соответствующий объём тестирования), также мы хотим доверять результатам работы сервиса проверки целостности обновления, поэтому он также будет доверенным.

![HLA-TCB](./diagrams/docs/report/hla-tcb/hla-tcb.png?raw=true "Доверенные компоненты")

Теоретически, шину обмена сообщениями можно сделать недоверенным компонентом, но тогда необходимо будет реализовать механим верификации сообщений. Например, можно использовать технологию типа blockchain. 
Цена этого изменения - усложнение обмена сообщениями, дополнительные накладные расходы на верификацию, снижение производительности системы, возможно также возникновение нестабильности и различные ситуации гонок.


### Политики безопасности 


```python {lineNo:true}

def check_operation(id, details):
    authorized = False
    src = details['source']
    dst = details['deliver_to']
    operation = details['operation']
    if  src == 'downloader' and dst == 'manager' \
        and operation == 'download_done':
        authorized = True   
    if src == 'manager' and dst == 'downloader' \
        and operation == 'download_file':
        authorized = True   
    if src == 'manager' and dst == 'storage' \
        and operation == 'commit_blob':
        authorized = True   
    if src == 'manager' and dst == 'verifier' \
        and operation == 'verification_requested':
        authorized = True   
    if src == 'verifier' and dst == 'manager' \
        and operation == 'handle_verification_result':
        authorized = True   
    if src == 'manager' and dst == 'updater' \
        and operation == 'proceed_with_update' \
        and details['verified'] is True:
        authorized = True   
    if src == 'storage' and dst == 'manager' \
        and operation == 'blob_committed':
        authorized = True   
    if src == 'verifier' and dst == 'storage' \
        and operation == 'get_blob':
        authorized = True
    if src == 'storage' and dst == 'verifier' \
        and operation == 'blob_content':
        authorized = True   
    if src == 'updater' and dst == 'storage' \
        and operation == 'get_blob':
        authorized = True
    if src == 'storage' and dst == 'updater' \
        and operation == 'blob_content':
        authorized = True   
     
    return authorized

```

## Запуск приложения и тестов

### Запуск приложения

см. [инструкцию по запуску](../../README.md)

### Запуск тестов

_Предполагается, что в ходе подготовки рабочего места все системные пакеты были установлены._

Запуск примера: открыть окно терминала в Visual Studio code, в папке secure-update с исходным кодом выполнить 

**make run**
или **docker-compose up -d**

Примечание: сервисам требуется некоторое время для начала обработки входящих сообщений от kafka, поэтому перед переходом к тестам следует сделать паузу 1-2 минуты

запуск тестов:
**make test**
или **pytest**
Ожидаемый результат (окно слева - вывод команды "docker-compose logs -f", окно справа - вывод команды "make test"): 
![pytest report](images/pytest-report.png "Логи сервисов и отчёт pytest")