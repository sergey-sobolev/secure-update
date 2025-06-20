# Отчёт о выполнении задачи "Secure update"

- [Отчёт о выполнении задачи "Secure update"](#отчёт-о-выполнении-задачи-secure-update)
  - [Постановка задачи\*](#постановка-задачи)
  - [Известные ограничения и вводные\*](#известные-ограничения-и-вводные)
    - [Цели и Предположения Безопасности (ЦПБ)\*](#цели-и-предположения-безопасности-цпб)
      - [Цели безопасности\*](#цели-безопасности)
      - [Предположения\*](#предположения)
  - [Архитектура решения\*](#архитектура-решения)
    - [Компоненты\*](#компоненты)
      - [Монитор безопасности (security monitor)](#монитор-безопасности-security-monitor)
    - [Алгоритм работы решения\*](#алгоритм-работы-решения)
    - [Описание cценариев (последовательности выполнения операций), при которых ЦБ нарушаются\*](#описание-cценариев-последовательности-выполнения-операций-при-которых-цб-нарушаются)
      - [Негативный сценарий 1. Менеджер не проверяет обновление](#негативный-сценарий-1-менеджер-не-проверяет-обновление)
      - [Негативный сценарий 2. Менеджер игнорирует результаты проверки](#негативный-сценарий-2-менеджер-игнорирует-результаты-проверки)
      - [Негативный сценарий 3. Storage подменяет файл после проверки](#негативный-сценарий-3-storage-подменяет-файл-после-проверки)
      - [Сводная таблица негативных сценариев\*](#сводная-таблица-негативных-сценариев)
    - [Политика архитектуры \*](#политика-архитектуры-)
      - [Обоснование политики архитектуры \*](#обоснование-политики-архитектуры-)
    - [Политики безопасности\*](#политики-безопасности)
  - [Запуск приложения и тестов\*](#запуск-приложения-и-тестов)
    - [Запуск приложения\*](#запуск-приложения)
    - [Запуск тестов\*](#запуск-тестов)

---
**Важно!** 
Отмеченные звёздочкой (*) пункты являются обязательными, их отсутствие приведёт к снижению оценки

---
## Постановка задачи*

Задача заключается в обновлении приложения (может быть прошивкой устройства), при условии, что файл обновления авторизован - то есть соответствует версии файла, полученной из доверенного источника (от поставщика обновления).

## Известные ограничения и вводные*

По условиям организаторов должна использоваться микросервисная архитектура и шина обмена сообщениями для реализации асинхронной работы сервисов.

### Цели и Предположения Безопасности (ЦПБ)*

#### Цели безопасности*

---
**Важно!**  Цели безопасности должны быть пронумерованы (даже если там всего один пункт). Ссылки на них ниже в тексте стоит делать по их номерам.

---

1. При любых обстоятельствах, для обновления приложения применяются только целостные прошивки

#### Предположения*

1. Физическая защищённость системы обеспечена

## Архитектура решения*

### Компоненты*

---
**Важно!** Обратите внимание, табличная форма описания важна для жюри.

---

| Название | Назначение | Комментарий |
|----|----|----|
|*File server* | хранит файлы с обновлением | внешний по отношению к системе сервис, имитатор сервера с обновлениями в интернете |
|*Application* | сервис с бизнес-логикой | заглушка |
|*Updater* | непосредственно применяет обновление | работает в одном контейнере с *Application*, чтобы иметь возможность обновлять его файлы |
|*Downloader*  | скачивает данные из сетей общего пользования | в примере скачивает данные с *File server* |
|*Manager* | оркестрирует весь процесс обновления | |
|*Verifier* | проверят корректность скачанного обновления | Теоретически, все проверки можно было бы вынести в Updater, но это сделало бы код данной сущности большим и сложным |
|*Storage* | осуществляет хранение скачанного обновления | |
|*Security monitor*<br>(монитор безопасности) | авторизует операцию, если она удовлетворяет заданным правилам или блокирует её в противном случае| |
|*Message bus* | шина сообщений и брокер - сервис передачи сообщений от источника получателям | kafka+zookeeper |
|

### Базовая архитектура

![HLA](./diagrams/docs/report/hla/hla_1.png?raw=true "Архитектура")


На логическом уровне коммуникация выглядит так

![SM](./diagrams/docs/report/sm/sm.png?raw=true "Монитор безопасности")

Т.е. менеджер обновлений поручает сервису verifier проверить обновление, которое тот берёт у сервиса storage, а монитор безопасности проверяет, что вся эта цепочка операций была проделана, и только в этом случае разрешает обратиться к сервису обновления.

### Алгоритм работы решения*

![Sequence diagram](./diagrams/sd.png?raw=true "Диаграмма вызовов")

### Описание cценариев (последовательности выполнения операций), при которых ЦБ нарушаются*

---
**Важно!**
Обратите внимание на формат описания негативных сценариев: каждый отдельный сценарий должен содержать
1. диаграмму последовательности вызовов, *на которой все скомпрометированные компоненты должны быть выделены красным цветом*, также *красным цветом следует выделить вредоносные шаги*
3. указание нарушенной цели безопасности (с её номером в разделе ЦПБ)

Примеры приведены ниже.

Несоблюдение этого формата может привести к потере очков при оценке.

---

Давайте посмотрим на процесс обновления с точки зрения безопасности, чтобы найти потенциальные проблемы, то есть сценарии, где возможна компрометации целей безопасности.

Наши вводные, исходя из выбранного охвата задач: на устройство доставлено обновление и теперь нам надо устройство обновить.

Первая значимая команда в диаграмме – это запрос на проверку и первая возможная проблема, компонент Manager «забыл» отправить запрос на проверку, и таким образом в результате на обновление отправится непроверенная версия.

Следующая значимая команда – запрос на обновление и следующая возможная проблема, это то, что результат проверки может быть проигнорирован и запрос на обновление может отправиться неверная версия обновления.

Следующая возможная проблема уже не связана командами, но она отражает тот факт, что между тем, как обновление проверено и запросом на обновление от Manager есть некий зазор по времени. В этот период времени данные обновления могут быть изменены, и на обновление может отправиться неверная версия обновления.

Детальный анализ может выявить ещё и другие проблемы, например, роллбэк атаку и т.д., но для понимания механизмов будет достаточно и самых очевидных. Поэтому, для упрощения политик безопасности примера мы будем рассматривать следующие три очевидных сценария:

1. «забыли» отправить запрос на проверку обновления;
2. результат проверки проигнорировали;
3. данные обновления изменили после проверки.
  
Ниже представлены три выбранные сценария компрометации целей безопасности на диаграмме процесса обновления:

![Негативные сценарии](./diagrams/sd-negative.png?raw=true "Негативные сценарии")

#### Негативный сценарий 1. Менеджер не проверяет обновление

![Негативный сценарий1](./diagrams/Hacked-manager1.png?raw=true "Менеджер не проверяет обновление")

Результат: недостижение цели безопасности №1: обновление не проверено, применена потенциально битая прошивка

#### Негативный сценарий 2. Менеджер игнорирует результаты проверки

![Негативный сценарий2](./diagrams/Hacked-manager2.png?raw=true "Менеджер игнорирует результаты проверки")

Результат: недостижение цели безопасности №1: возможно обновление некорректным файлом


#### Негативный сценарий 3. Storage подменяет файл после проверки

![Негативный сценарий3](./diagrams/Hacked-manager3.png?raw=true "Storage подменяет файл после проверки")

Результат: недостижение цели безопасности №1: обновление некорректным файлом

#### Сводная таблица негативных сценариев*

|№  | Название | Скомпрометированная часть системы | Нарушенная цель безопасности |
|----|----|----|----|
|1 | Менеджер не проверяет обновление | Manager | 1 |
|2 | Менеджер игнорирует результат проверки | Manager | 1 |
|3 | Storage подменяет файл после проверки  | Storage | 1 |


### Политика архитектуры *

---
**Важно!** Должна быть диаграмма, а не только текстовое описание.

---

В общем случае, компонент Manager может быть недоверенным, результаты проверки могут быть игнорированы или данные могут изменены после проверки.

Так как шина обмена сообщений и монитор безопасности являются общесистемными, они являются доверенными по умолчанию и на диаграмме не отображаются.



![DFD-TCB](./diagrams/architecture-policy.png?raw=true "Доверенные компоненты на диаграмме потоков данных")

#### Обоснование политики архитектуры *

|ЦБ№  | ЦБ | Компонент | Уровень доверия | Обоснование |
|----|----|----|----|----|
| 1 | Для обновления приложения применяются только целостные прошивки | Verifier | доверенный, повышающий целостность данных | этот компонент отвечает за проверку целостности и фиксирование результатов проверки (опечатывание), это критично для ЦБ1
| 1 | Для обновления приложения применяются только целостные прошивки | Updater | доверенный, повышающий целостность данных | этот компонент получает запрос от недоверенного менеджера обновлений, поэтому должен осуществлять дополнительный контроль данных, также он не может быть недоверенным, иначе, теоретически, он может обновить приложение произвольными данными |
|ЦБ не нарушены || Manager | недоверенный | худшее, что сможет сделать - изменить файл, но это будет обнаружено Verifier или Updater |
|ЦБ не нарушены || Storage | недоверенный | худшее, что сможет сделать - изменить файл, но это будет обнаружено Verifier или Updater |
|ЦБ не нарушены || Downloader | недоверенный | худшее, что сможет сделать - изменить файл, но это будет обнаружено Verifier или Updater |

### Политики безопасности*


```python {lineNo:true}

import base64
VERIFIER_SEAL = 'verifier_seal'


def check_operation(id, details):
    authorized = False
    # print(f"[debug] checking policies for event {id}, details: {details}")
    print(f"[info] checking policies for event {id},"
          f" {details['source']}->{details['deliver_to']}: {details['operation']}")
    src = details['source']
    dst = details['deliver_to']
    operation = details['operation']
    if src == 'downloader' and dst == 'manager' \
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
    if src == 'storage' and dst == 'verifier' \
            and operation == 'blob_committed':
        authorized = True
    if src == 'verifier' and dst == 'storage' \
            and operation == 'get_blob':
        authorized = True
    if src == 'verifier' and dst == 'storage' \
            and operation == 'commit_sealed_blob' \
            and details['verified'] is True:
        authorized = True
    if src == 'storage' and dst == 'verifier' \
            and operation == 'blob_content':
        authorized = True
    if src == 'updater' and dst == 'storage' \
            and operation == 'get_blob':
        authorized = True
    if src == 'storage' and dst == 'updater' \
            and operation == 'blob_content' and check_payload_seal(details['blob']) is True:
        authorized = True

    return authorized


def check_payload_seal(payload):
    try:
        p = base64.b64decode(payload).decode()
        if p.endswith(VERIFIER_SEAL):
            print('[info] payload seal is valid')
            return True
    except Exception as e:
        print(f'[error] seal check error: {e}')
        return False


```

## Запуск приложения и тестов*

---
**Важно!** Отсутствие 
- понятного описания ручного тестирования приложения 
- автоматических тестов 

для проверки функционала и негативных сценариев приведёт к существенному снижению оценки работы команды.

---

### Запуск приложения*

см. [инструкцию по запуску](../../README.md)

### Запуск тестов*

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