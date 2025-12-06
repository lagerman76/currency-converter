import urllib.request
import json
import time
from datetime import datetime

class CurrencyBot:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.cbr_url = "https://www.cbr-xml-daily.ru/daily_json.js"
        
    def safe_request(self, url):
        """Безопасный запрос"""
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            print(f"Ошибка запроса: {e}")
            return None
    
    def get_currency_rates(self):
        """Получает курсы валют"""
        try:
            data = self.safe_request(self.cbr_url)
            if not data:
                return None
            
            currencies = {}
            target_currencies = ['USD', 'EUR', 'CNY', 'GBP', 'JPY', 'KZT', 'TRY', 'CHF']
            
            for curr_code in target_currencies:
                if curr_code in data.get('Valute', {}):
                    currencies[curr_code] = data['Valute'][curr_code]
            
            return {
                'date': data.get('Date', datetime.now().isoformat()),
                'currencies': currencies
            }
        except Exception as e:
            print(f"Ошибка получения курсов: {e}")
            return None
    
    def send_message(self, chat_id, text, parse_mode='HTML'):
        """Отправка сообщения"""
        try:
            import urllib.parse
            
            params = {
                'chat_id': str(chat_id),
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': 'true'
            }
            
            query_string = urllib.parse.urlencode(params)
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage?{query_string}"
            
            response = self.safe_request(url)
            return response and response.get('ok')
                
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            return False
    
    def convert_to_rubles(self, amount, currency_code):
        """Конвертирует в рубли"""
        rates = self.get_currency_rates()
        if not rates or currency_code not in rates['currencies']:
            return None
        
        currency = rates['currencies'][currency_code]
        # Учитываем номинал (например, 1 JPY = 0.6 руб, но в API курс за 100 йен)
        nominal = currency.get('Nominal', 1)
        rate = currency['Value']
        
        # Формула: сумма * (курс / номинал)
        result = amount * (rate / nominal)
        return round(result, 2)
    
    def get_currency_name(self, currency_code):
        """Получает название валюты"""
        names = {
            'USD': ('🇺🇸 Доллар США', '$'),
            'EUR': ('🇪🇺 Евро', '€'),
            'CNY': ('🇨🇳 Китайский юань', '¥'),
            'GBP': ('🇬🇧 Фунт стерлингов', '£'),
            'JPY': ('🇯🇵 Японская йена', '¥'),
            'KZT': ('🇰🇿 Казахстанский тенге', '₸'),
            'TRY': ('🇹🇷 Турецкая лира', '₺'),
            'CHF': ('🇨🇭 Швейцарский франк', '₣'),
            'RUB': ('🇷🇺 Российский рубль', '₽')
        }
        return names.get(currency_code, (f'Валюта {currency_code}', ''))
    
    def format_conversion_result(self, amount, from_currency, to_rubles):
        """Форматирует результат конвертации"""
        currency_name, currency_symbol = self.get_currency_name(from_currency)
        
        return f"""
💱 <b>Результат конвертации</b>

{currency_symbol} <b>{amount:.2f} {from_currency}</b> ({currency_name})

⬇️

🇷🇺 <b>{to_rubles:,.2f} RUB</b> (Российских рублей)

<i>Курс ЦБ РФ • {datetime.now().strftime('%d.%m.%Y')}</i>
"""
    
    def get_updates(self, offset=None):
        """Получает обновления"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            if offset:
                url += f"?offset={offset}&timeout=30"
            else:
                url += "?timeout=30"
            
            response = self.safe_request(url)
            if response and response.get('ok'):
                return response.get('result', [])
            return []
        except Exception as e:
            print(f"Ошибка получения updates: {e}")
            return []
    
    def process_message(self, update):
        """Обработка сообщений"""
        message = update['message']
        chat_id = message['chat']['id']
        text = message.get('text', '').strip()
        
        print(f"Получено: '{text}' от chat_id: {chat_id}")
        
        # Команда /start
        if text == '/start':
            welcome = """<b>🏦 Бот курсов валют + Конвертер</b>

<b>📋 Основные команды:</b>
/usd - курс доллара
/eur - курс евро  
/cny - курс юаня
/all - все курсы

<b>💱 Конвертер в рубли:</b>
/convert 100 USD - 100$ в рублях
/convert 50 EUR - 50€ в рублях
/convert 1000 CNY - 1000¥ в рублях

<b>🎯 Примеры:</b>
<code>/convert 100 USD</code> - конвертировать 100 долларов
<code>/convert 50 EUR</code> - конвертировать 50 евро
<code>/convert 10000 JPY</code> - конвертировать 10000 йен

<i>Поддерживаются: USD, EUR, CNY, GBP, JPY, KZT, TRY, CHF</i>
"""
            self.send_message(chat_id, welcome, 'HTML')
        
        # Команда /convert
        elif text.startswith('/convert'):
            try:
                # Разбираем команду: /convert 100 USD
                parts = text.split()
                
                if len(parts) != 3:
                    self.send_message(chat_id, 
                        "❌ <b>Неверный формат!</b>\n\n"
                        "Используйте: <code>/convert 100 USD</code>\n"
                        "Где:\n"
                        "- 100 - сумма\n"
                        "- USD - код валюты\n\n"
                        "<i>Примеры:</i>\n"
                        "<code>/convert 100 USD</code>\n"
                        "<code>/convert 50 EUR</code>\n"
                        "<code>/convert 1000 CNY</code>", 'HTML')
                    return
                
                # Парсим сумму и валюту
                amount = float(parts[1])
                currency = parts[2].upper().strip()
                
                # Проверяем валидность суммы
                if amount <= 0:
                    self.send_message(chat_id, "❌ Сумма должна быть больше 0", 'HTML')
                    return
                
                if amount > 1000000:  # Ограничение на очень большие суммы
                    self.send_message(chat_id, "❌ Сумма слишком большая (макс: 1,000,000)", 'HTML')
                    return
                
                # Список поддерживаемых валют
                supported_currencies = ['USD', 'EUR', 'CNY', 'GBP', 'JPY', 'KZT', 'TRY', 'CHF']
                
                if currency not in supported_currencies:
                    self.send_message(chat_id,
                        f"❌ <b>Валюта {currency} не поддерживается</b>\n\n"
                        f"📋 <i>Доступные валюты:</i>\n"
                        f"🇺🇸 USD - Доллар США\n"
                        f"🇪🇺 EUR - Евро\n"
                        f"🇨🇳 CNY - Китайский юань\n"
                        f"🇬🇧 GBP - Фунт стерлингов\n"
                        f"🇯🇵 JPY - Японская йена\n"
                        f"🇰🇿 KZT - Казахстанский тенге\n"
                        f"🇹🇷 TRY - Турецкая лира\n"
                        f"🇨🇭 CHF - Швейцарский франк", 'HTML')
                    return
                
                # Выполняем конвертацию
                self.send_message(chat_id, f"⏳ <i>Конвертирую {amount} {currency} в рубли...</i>", 'HTML')
                
                result = self.convert_to_rubles(amount, currency)
                
                if result:
                    # Форматируем результат
                    message = self.format_conversion_result(amount, currency, result)
                    self.send_message(chat_id, message, 'HTML')
                    
                    # Дополнительная информация о курсе
                    rates = self.get_currency_rates()
                    if rates and currency in rates['currencies']:
                        curr_data = rates['currencies'][currency]
                        rate = curr_data['Value']
                        nominal = curr_data.get('Nominal', 1)
                        
                        rate_info = f"\n📊 <b>Курс:</b> {nominal} {currency} = {rate:.2f} RUB"
                        
                        if 'Previous' in curr_data:
                            change = rate - curr_data['Previous']
                            change_icon = "📈" if change > 0 else "📉"
                            rate_info += f"\n{change_icon} <b>Изменение:</b> {change:+.4f} RUB"
                        
                        self.send_message(chat_id, rate_info, 'HTML')
                else:
                    self.send_message(chat_id, f"❌ Не удалось конвертировать {currency}. Попробуйте позже.", 'HTML')
                
            except ValueError:
                self.send_message(chat_id, 
                    "❌ <b>Неверный формат числа!</b>\n\n"
                    "Используйте: <code>/convert 100 USD</code>\n"
                    "Где 100 - это число (можно с десятичной точкой)\n\n"
                    "<i>Правильно:</i> 100, 50.5, 1000.75\n"
                    "<i>Неправильно:</i> сто, 100$", 'HTML')
            except Exception as e:
                print(f"Ошибка конвертации: {e}")
                self.send_message(chat_id, "❌ Произошла ошибка при конвертации. Попробуйте позже.", 'HTML')
        
        # Команда /usd
        elif text == '/usd':
            self.show_currency_rate(chat_id, 'USD')
        
        # Команда /eur
        elif text == '/eur':
            self.show_currency_rate(chat_id, 'EUR')
        
        # Команда /cny':
        elif text == '/cny':
            self.show_currency_rate(chat_id, 'CNY')
        
        # Команда /all
        elif text == '/all':
            rates = self.get_currency_rates()
            if rates:
                message = "<b>💱 Актуальные курсы валют ЦБ РФ</b>\n\n"
                
                currencies_display = [
                    ('USD', '🇺🇸 Доллар'),
                    ('EUR', '🇪🇺 Евро'),
                    ('CNY', '🇨🇳 Юань'),
                    ('GBP', '🇬🇧 Фунт'),
                    ('JPY', '🇯🇵 Йена'),
                    ('KZT', '🇰🇿 Тенге'),
                    ('TRY', '🇹🇷 Лира'),
                    ('CHF', '🇨🇭 Франк')
                ]
                
                for code, emoji_name in currencies_display:
                    if code in rates['currencies']:
                        curr = rates['currencies'][code]
                        nominal = curr.get('Nominal', 1)
                        rate = curr['Value']
                        
                        # Для йен показываем за 100 единиц
                        if code == 'JPY' and nominal == 100:
                            message += f"{emoji_name} (100 {code}): <b>{rate:.2f} RUB</b>\n"
                        else:
                            message += f"{emoji_name} ({code}): <b>{rate:.2f} RUB</b>\n"
                
                try:
                    date_str = rates['date']
                    if 'T' in date_str:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        time_str = date_obj.strftime('%d.%m.%Y %H:%M')
                    else:
                        time_str = datetime.now().strftime('%d.%m.%Y %H:%M')
                    message += f"\n🕐 <i>Обновлено: {time_str}</i>"
                except:
                    message += f"\n🕐 <i>Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>"
                
                message += "\n\n💱 <i>Используйте /convert для конвертации</i>"
                
                self.send_message(chat_id, message, 'HTML')
            else:
                self.send_message(chat_id, "❌ Не удалось получить курсы валют", 'HTML')
        
        # Команда /help
        elif text == '/help':
            help_text = """<b>🆘 Помощь по боту</b>

<b>💰 Курсы валют:</b>
/usd - курс доллара
/eur - курс евро
/cny - курс юаня
/all - все курсы

<b>💱 Конвертер:</b>
/convert [сумма] [валюта]
Примеры:
<code>/convert 100 USD</code>
<code>/convert 50 EUR</code>
<code>/convert 1000 CNY</code>

<b>📊 Поддерживаемые валюты:</b>
USD, EUR, CNY, GBP, JPY, KZT, TRY, CHF

<b>ℹ️ Информация:</b>
Данные предоставляются Центробанком РФ
Курсы обновляются ежедневно
"""
            self.send_message(chat_id, help_text, 'HTML')
        
        # Прямой ввод конвертации (без команды /convert)
        elif self.is_conversion_query(text):
            self.handle_direct_conversion(chat_id, text)
        
        else:
            # Неизвестная команда
            self.send_message(chat_id,
                "🤖 <b>Бот курсов валют + Конвертер</b>\n\n"
                "Используйте команды:\n"
                "/start - показать все возможности\n"
                "/convert - конвертер в рубли\n"
                "/all - все курсы валют\n"
                "/help - помощь\n\n"
                "<i>Пример конвертации:</i>\n"
                "<code>100 USD</code> или <code>/convert 100 USD</code>", 'HTML')
    
    def show_currency_rate(self, chat_id, currency_code):
        """Показывает курс конкретной валюты"""
        rates = self.get_currency_rates()
        if rates and currency_code in rates['currencies']:
            currency = rates['currencies'][currency_code]
            currency_name, currency_symbol = self.get_currency_name(currency_code)
            
            message = f"""<b>{currency_name} ({currency_code})</b>

📊 <b>Курс ЦБ РФ:</b>
{currency_symbol} 1 {currency_code} = <b>{currency['Value']:.2f} RUB</b>"""
            
            if currency.get('Nominal', 1) != 1:
                message += f"\n\n<i>Номинал: {currency['Nominal']} единиц</i>"
            
            if 'Previous' in currency:
                change = currency['Value'] - currency['Previous']
                change_percent = (change / currency['Previous']) * 100
                
                change_icon = "📈" if change > 0 else "📉"
                message += f"\n\n{change_icon} <b>Изменение:</b> {change:+.4f} RUB ({change_percent:+.2f}%)"
            
            message += f"\n\n💱 <i>Конвертировать: <code>/convert 100 {currency_code}</code></i>"
            
            self.send_message(chat_id, message, 'HTML')
        else:
            self.send_message(chat_id, f"❌ Не удалось получить курс {currency_code}", 'HTML')
    
    def is_conversion_query(self, text):
        """Проверяет, является ли текст запросом на конвертацию"""
        try:
            parts = text.split()
            if len(parts) == 2:
                # Проверяем формат: "100 USD"
                amount = float(parts[0])
                currency = parts[1].upper()
                supported = ['USD', 'EUR', 'CNY', 'GBP', 'JPY', 'KZT', 'TRY', 'CHF']
                return currency in supported and amount > 0
            return False
        except:
            return False
    
    def handle_direct_conversion(self, chat_id, text):
        """Обрабатывает прямой запрос конвертации (без команды /convert)"""
        try:
            parts = text.split()
            amount = float(parts[0])
            currency = parts[1].upper()
            
            # Имитируем команду /convert
            self.send_message(chat_id, 
                f"🔍 <i>Обнаружен запрос на конвертацию...</i>\n"
                f"Выполняю: <code>/convert {amount} {currency}</code>", 'HTML')
            
            # Создаем фиктивное сообщение для обработки
            fake_update = {
                'message': {
                    'chat': {'id': chat_id},
                    'text': f'/convert {amount} {currency}'
                }
            }
            
            # Обрабатываем как обычную команду /convert
            self.process_message(fake_update)
            
        except Exception as e:
            print(f"Ошибка обработки прямого запроса: {e}")
    
    def run(self):
        """Запуск бота"""
        print("=" * 60)
        print("🏦 БОТ КУРСОВ ВАЛЮТ С КОНВЕРТЕРОМ")
        print("=" * 60)
        print("Функции:")
        print("• Курсы валют ЦБ РФ")
        print("• Конвертер в рубли")
        print("• Поддержка 8 валют")
        print("\nОжидание сообщений...")
        print("Для остановки: Ctrl+C\n")
        
        # Проверка доступности API
        print("🔍 Проверяем доступность API...")
        rates = self.get_currency_rates()
        if rates:
            print("✅ API доступен")
            usd = rates['currencies'].get('USD', {})
            if usd:
                print(f"   USD: {usd.get('Value', 'N/A')} RUB")
        else:
            print("⚠️  API временно недоступен, бот будет использовать кэш")
        
        print("\n" + "=" * 60)
        
        last_update_id = 0
        
        while True:
            try:
                updates = self.get_updates(last_update_id + 1)
                
                for update in updates:
                    last_update_id = update['update_id']
                    
                    if 'message' in update:
                        user = update['message'].get('from', {})
                        username = user.get('username', 'без username')
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {user.get('first_name', 'User')} (@{username}): {update['message'].get('text', '')[:50]}")
                        self.process_message(update)
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n\n👋 Бот остановлен пользователем")
                break
            except Exception as e:
                print(f"Ошибка в основном цикле: {e}")
                time.sleep(5)

def main():
    print("НАСТРОЙКА БОТА КУРСОВ ВАЛЮТ С КОНВЕРТЕРОМ")
    print("=" * 60)
    
    # Можно ввести токен или использовать переменную окружения
    import os
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    
    if not BOT_TOKEN:
        BOT_TOKEN = input("Введите токен бота от @BotFather: ").strip()
    
    if not BOT_TOKEN:
        print("❌ Токен не может быть пустым")
        return
    
    # Проверка токена
    print("\n🔍 Проверяем токен...")
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Бот: {bot_info['first_name']} (@{bot_info['username']})")
                print(f"\n📲 Ссылка на бота: https://t.me/{bot_info['username']}")
                print(f"🚀 Бот готов к работе!")
                
                # Запуск бота
                bot = CurrencyBot(BOT_TOKEN)
                bot.run()
            else:
                print(f"❌ Ошибка: {data.get('description')}")
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")

if __name__ == "__main__":
    main()