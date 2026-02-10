from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Создает группу менеджеров с нужными правами"

    def handle(self, *args, **options):
        from django.contrib.auth.models import Group, Permission

        managers_group, created = Group.objects.get_or_create(name="Менеджеры")

        if created:
            self.stdout.write('Группа "Менеджеры" создана')
        else:
            self.stdout.write('ℹГруппа "Менеджеры" уже существует')

        view_permissions = Permission.objects.filter(codename__startswith="view_")

        special_permissions = ["disable_mailing"]

        for codename in special_permissions:
            try:
                perm = Permission.objects.get(codename=codename)
                view_permissions = view_permissions | Permission.objects.filter(
                    id=perm.id
                )
            except Permission.DoesNotExist:
                self.stdout.write(f"Право {codename} не найдено")

        managers_group.permissions.set(view_permissions)

        self.stdout.write(
            self.style.SUCCESS(
                f'Добавлено {view_permissions.count()} прав для группы "Менеджеры"'
            )
        )

        self.stdout.write("\nДля создания менеджера:")
        self.stdout.write("1. python manage.py createsuperuser")
        self.stdout.write("2. Зайдите в админку: http://127.0.0.1:8000/admin/")
        self.stdout.write("3. Группы → Менеджеры → Добавить пользователя")
