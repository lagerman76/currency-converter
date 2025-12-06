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
            target_currencies = ['USD', 'EUR', 'CNY', 'GBP', 'JPY']
            
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
        """Правильная отправка сообщения"""
        try:
            import urllib.parse
            
            # Кодируем только URL, а не текст целиком
            params = {
                'chat_id': str(chat_id),
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': 'true'
            }
            
            # Создаем строку запроса
            query_string = urllib.parse.urlencode(params)
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage?{query_string}"
            
            response = self.safe_request(url)
            if response and response.get('ok'):
                return True
            else:
                error = response.get('description', 'Unknown error') if response else 'No response'
                print(f"Ошибка отправки: {error}")
                return False
                
        except Exception as e:
            print(f"Ошибка в send_message: {e}")
            return False
    
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
        
        print(f"Получено сообщение: '{text}' от chat_id: {chat_id}")
        
        if text == '/start':
            # ✅ ПРАВИЛЬНЫЙ ФОРМАТ HTML (без лишнего экранирования)
            welcome = """<b>🏦 Бот курсов валют</b>

<b>📋 Команды:</b>
/start - показать это сообщение
/usd - курс доллара
/eur - курс евро  
/cny - курс юаня
/all - все курсы

<i>Данные от Центробанка РФ</i>"""
            
            self.send_message(chat_id, welcome, 'HTML')
        
        elif text == '/usd':
            rates = self.get_currency_rates()
            if rates and 'USD' in rates['currencies']:
                usd = rates['currencies']['USD']
                message = f"🇺🇸 <b>Доллар (USD)</b>\nКурс: <b>{usd['Value']:.2f} ₽</b>"
                self.send_message(chat_id, message, 'HTML')
            else:
                self.send_message(chat_id, "Не удалось получить курс доллара")
        
        elif text == '/eur':
            rates = self.get_currency_rates()
            if rates and 'EUR' in rates['currencies']:
                eur = rates['currencies']['EUR']
                message = f"🇪🇺 <b>Евро (EUR)</b>\nКурс: <b>{eur['Value']:.2f} ₽</b>"
                self.send_message(chat_id, message, 'HTML')
            else:
                self.send_message(chat_id, "Не удалось получить курс евро")
        
        elif text == '/cny':
            rates = self.get_currency_rates()
            if rates and 'CNY' in rates['currencies']:
                cny = rates['currencies']['CNY']
                message = f"🇨🇳 <b>Юань (CNY)</b>\nКурс: <b>{cny['Value']:.2f} ₽</b>"
                self.send_message(chat_id, message, 'HTML')
            else:
                self.send_message(chat_id, "Не удалось получить курс юаня")
        
        elif text == '/all':
            rates = self.get_currency_rates()
            if rates:
                message = "<b>💱 Курсы валют ЦБ РФ</b>\n\n"
                for code in ['USD', 'EUR', 'CNY']:
                    if code in rates['currencies']:
                        curr = rates['currencies'][code]
                        # Простые эмодзи и форматирование
                        emoji = {'USD': '🇺🇸', 'EUR': '🇪🇺', 'CNY': '🇨🇳'}.get(code, '💰')
                        message += f"{emoji} <b>{code}:</b> {curr['Value']:.2f} ₽\n"
                
                # Добавляем время
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
                
                self.send_message(chat_id, message, 'HTML')
            else:
                self.send_message(chat_id, "Не удалось получить курсы валют")
        
        else:
            # Для неизвестных команд
            help_text = """🤖 <b>Бот курсов валют</b>

Используйте команды:
/usd - курс доллара
/eur - курс евро
/cny - курс юаня
/all - все курсы

Или отправьте /start для полного списка команд"""
            self.send_message(chat_id, help_text, 'HTML')
    
    def run(self):
        """Запуск бота"""
        print("=" * 50)
        print("🏦 БОТ КУРСОВ ВАЛЮТ ЗАПУЩЕН")
        print("=" * 50)
        print("Ожидание сообщений...")
        print("Для остановки нажмите Ctrl+C\n")
        
        last_update_id = 0
        
        while True:
            try:
                updates = self.get_updates(last_update_id + 1)
                
                for update in updates:
                    last_update_id = update['update_id']
                    
                    if 'message' in update:
                        self.process_message(update)
                
                time.sleep(0.1)  # Короткая пауза
                
            except KeyboardInterrupt:
                print("\n\n👋 Бот остановлен")
                break
            except Exception as e:
                print(f"Ошибка: {e}")
                time.sleep(5)

def main():
    print("НАСТРОЙКА БОТА КУРСОВ ВАЛЮТ")
    print("=" * 50)
    
    # Введите токен
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
                
                # Запуск бота
                bot = CurrencyBot(BOT_TOKEN)
                bot.run()
            else:
                print(f"❌ Ошибка: {data.get('description')}")
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")

if __name__ == "__main__":
    main()