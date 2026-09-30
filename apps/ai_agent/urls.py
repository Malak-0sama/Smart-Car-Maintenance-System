from django.urls import path
from . import views

app_name = "ai_agent"

urlpatterns = [
    path("chat/", views.chat_page_view, name="chat_page"),
    path("api/message/", views.chat_message_view, name="chat_message"),
]
