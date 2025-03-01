from django.urls import path
from .views import DailyPuzzleView, ValidateAnswersView

urlpatterns = [
    path('daily/', DailyPuzzleView.as_view(), name='daily-puzzle'),
    path('validate/', ValidateAnswersView.as_view(), name='validate-answers'),
]