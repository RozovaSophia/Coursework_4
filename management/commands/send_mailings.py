from django.core.management.base import BaseCommand
from django.utils import timezone
import random


class Command(BaseCommand):
    help = "Отправляет все активные рассылки"

    def add_arguments(self, parser):
        parser.add_argument(
            "--mailing-id", type=int, help="ID конкретной рассылки для отправки"
        )

    def handle(self, *args, **options):
        from mailing.models import Mailing, MailingAttempt

        mailing_id = options.get("mailing_id")

        if mailing_id:
            try:
                mailing = Mailing.objects.get(id=mailing_id)
                self.send_mailing(mailing)
            except Mailing.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ Рассылка {mailing_id} не найдена")
                )
        else:
            now = timezone.now()
            active_mailings = Mailing.objects.filter(
                start_time__lte=now, end_time__gte=now
            )

            self.stdout.write(f"📊 Найдено {active_mailings.count()} активных рассылок")

            for mailing in active_mailings:
                self.send_mailing(mailing)

    def send_mailing(self, mailing):
        """Имитация отправки рассылки"""
        from mailing.models import MailingAttempt

        success_count = 0
        failure_count = 0

        for client in mailing.clients.all():
            if random.random() < 0.8:
                status = "Успешно"
                response = f"Письмо отправлено на {client.email}"
                success_count += 1
            else:
                status = "Не успешно"
                response = "Ошибка SMTP сервера"
                failure_count += 1

            MailingAttempt.objects.create(
                mailing=mailing, status=status, server_response=response
            )

        result = (
            f"✅ Рассылка {mailing.id}: Успешно {success_count}, Ошибок {failure_count}"
        )
        self.stdout.write(self.style.SUCCESS(result))
        return True
