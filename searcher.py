import asyncio
import logging
import threading

from telethon import TelegramClient
from telethon.errors import FloodWaitError, UsernameNotOccupiedError, UsernameInvalidError

from utils import generate_username, is_liquid_username

logger = logging.getLogger(__name__)

class SearchEngine(threading.Thread):
    """
    Поток, выполняющий генерацию и проверку username через Telegram API.
    """
    def __init__(self, api_id, api_hash, params, on_result, on_status, on_error):
        super().__init__(daemon=True)
        self.api_id = api_id
        self.api_hash = api_hash
        self.params = params  # dict: length, allow_digits, allow_uppercase
        self.on_result = on_result  # callback(username, status, is_liquid)
        self.on_status = on_status  # callback(message)
        self.on_error = on_error    # callback(error_message)
        self.running = False
        self.client = None
        self.loop = None

    def stop(self):
        self.running = False

    def run(self):
        self.running = True
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._async_run())
        except Exception as e:
            logger.exception("Ошибка в поисковом потоке")
            self.on_error(f"Ошибка: {e}")
        finally:
            if self.client:
                self.loop.run_until_complete(self.client.disconnect())
            self.loop.close()
            self.running = False

    async def _async_run(self):
        self.client = TelegramClient('session', self.api_id, self.api_hash)
        await self.client.start()
        logger.info("Клиент Telegram авторизован")
        self.on_status("Подключено, начинаем поиск...")

        total_checked = 0
        free_found = 0
        deleted_found = 0

        while self.running:
            username = generate_username(
                length=self.params['length'],
                allow_digits=self.params['allow_digits'],
                allow_uppercase=self.params['allow_uppercase']
            )

            status = await self._async_check_username(username)
            total_checked += 1

            if status == 'free':
                free_found += 1
                liquid = is_liquid_username(username)
                self.on_result(username, 'free', liquid)
            elif status == 'deleted':
                deleted_found += 1
                liquid = is_liquid_username(username)
                self.on_result(username, 'deleted', liquid)

            status_msg = (f"Проверено: {total_checked}, "
                          f"свободных: {free_found}, "
                          f"удалённых: {deleted_found}, "
                          f"текущий: {username}")
            self.on_status(status_msg)

            await asyncio.sleep(0.7)

        self.on_status(f"Поиск остановлен. Проверено: {total_checked}, "
                       f"свободных: {free_found}, удалённых: {deleted_found}")

    async def _async_check_username(self, username):
        attempt = 0
        max_attempts = 3
        while attempt < max_attempts:
            try:
                entity = await self.client.get_entity(username)
                if hasattr(entity, 'deleted') and entity.deleted:
                    return 'deleted'
                return 'taken'
            except (UsernameNotOccupiedError, UsernameInvalidError, ValueError):
                return 'free'
            except FloodWaitError as e:
                logger.warning(f"Flood wait: {e.seconds} секунд")
                await asyncio.sleep(e.seconds)
                continue
            except Exception as e:
                logger.error(f"Ошибка при проверке {username}: {e}")
                attempt += 1
                if attempt < max_attempts:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return 'error'
        return 'error'
