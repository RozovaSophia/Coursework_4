from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
)
from django.urls import reverse_lazy
from .models import Client, Message, Mailing, MailingAttempt
from .forms import ClientForm, MessageForm, MailingForm


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = "mailing/client_list.html"

    def get_queryset(self):
        if self.request.user.groups.filter(name="Менеджеры").exists():
            return Client.objects.all()
        return Client.objects.filter(owner=self.request.user)


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")

    def get_queryset(self):
        return Client.objects.filter(owner=self.request.user)


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = "mailing/client_confirm_delete.html"
    success_url = reverse_lazy("mailing:client_list")

    def get_queryset(self):
        return Client.objects.filter(owner=self.request.user)


class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = "mailing/message_list.html"

    def get_queryset(self):
        if self.request.user.groups.filter(name="Менеджеры").exists():
            return Message.objects.all()
        return Message.objects.filter(owner=self.request.user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = "mailing/message_confirm_delete.html"
    success_url = reverse_lazy("mailing:message_list")

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)


class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "mailing/mailing_list.html"

    def get_queryset(self):
        if self.request.user.groups.filter(name="Менеджеры").exists():
            return Mailing.objects.all()
        return Mailing.objects.filter(owner=self.request.user)


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    model = Mailing
    template_name = "mailing/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)


class AttemptListView(LoginRequiredMixin, ListView):
    model = MailingAttempt
    template_name = "mailing/attempt_list.html"

    def get_queryset(self):
        if self.request.user.groups.filter(name="Менеджеры").exists():
            return MailingAttempt.objects.all()
        return MailingAttempt.objects.filter(mailing__owner=self.request.user)


from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .services import send_mailing_now


def send_mailing_view(request, pk):
    if not request.user.is_authenticated:
        return redirect("users:login")

    mailing = get_object_or_404(Mailing, pk=pk)

    if (
        not request.user.groups.filter(name="Менеджеры").exists()
        and mailing.owner != request.user
    ):
        messages.error(request, "Нет прав")
        return redirect("mailing:mailing_list")

    success, result = send_mailing_now(mailing)

    if success:
        messages.success(request, f"Рассылка отправлена: {result}")
    else:
        messages.error(request, f"Ошибка: {result}")

    return redirect("mailing:mailing_list")


from django.shortcuts import render
from django.utils import timezone


def home(request):
    from .models import Mailing, Client

    context = {
        "total_mailings": Mailing.objects.count(),
        "active_mailings": Mailing.objects.filter(
            start_time__lte=timezone.now(), end_time__gte=timezone.now()
        ).count(),
        "unique_clients": Client.objects.values("email").distinct().count(),
    }
    return render(request, "home.html", context)


from django.db.models import Count, Q


def statistics_view(request):
    if not request.user.is_authenticated:
        return redirect("users:login")

    from .models import MailingAttempt

    if request.user.groups.filter(name="Менеджеры").exists():
        attempts = MailingAttempt.objects.all()
    else:
        attempts = MailingAttempt.objects.filter(mailing__owner=request.user)

    total_attempts = attempts.count()
    successful_attempts = attempts.filter(status="Успешно").count()
    failed_attempts = attempts.filter(status="Не успешно").count()

    mailing_stats = attempts.values(
        "mailing__id", "mailing__message__subject"
    ).annotate(
        total=Count("id"),
        success=Count("id", filter=Q(status="Успешно")),
        failed=Count("id", filter=Q(status="Не успешно")),
    )

    context = {
        "total_attempts": total_attempts,
        "successful_attempts": successful_attempts,
        "failed_attempts": failed_attempts,
        "mailing_stats": mailing_stats,
    }

    return render(request, "mailing/statistics.html", context)
