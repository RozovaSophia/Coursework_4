from django.core.mail import send_mail
from django.utils import timezone
from .models import MailingAttempt


def send_mailing_now(mailing):
    """Отправляет рассылку сейчас"""
    now = timezone.now()

    if not (mailing.start_time <= now <= mailing.end_time):
        return False, "Не время для отправки"

    success_count = 0
    failure_count = 0

    for client in mailing.clients.all():
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email="noreply@example.com",
                recipient_list=[client.email],
                fail_silently=False,
            )
            status = "Успешно"
            response = "Отправлено"
            success_count += 1
        except Exception as e:
            status = "Не успешно"
            response = str(e)
            failure_count += 1

        MailingAttempt.objects.create(
            mailing=mailing, status=status, server_response=response
        )

    return True, f"Успешно: {success_count}, Ошибок: {failure_count}"
