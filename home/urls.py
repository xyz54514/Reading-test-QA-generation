from django.urls import path
from . import views

urlpatterns = [
    path('', views.go_home, name='go_home'),
    path('teacher_login_/', views.teacher_login_, name='teacher_login_'),
    path('teacher_login/', views.teacher_login, name='teacher_login'),
    path('teacher_register/', views.teacher_register, name='teacher_register'),
    path('teacher_create/', views.teacher_create, name='teacher_create'),
    path('teacher_create_/', views.teacher_create_, name='teacher_create_'),
    path('go_passage/', views.go_passage, name='go_passage'),
    path('go_passage_explain/', views.go_passage_explain, name='go_passage_explain'),
    path('teacher_check_qa_/', views.teacher_check_qa_, name='teacher_check_qa_'),
    path('open_teacher_check_qa/', views.open_teacher_check_qa, name='open_teacher_check_qa'),
    path('teacher_edit_/', views.teacher_edit_, name='teacher_edit_'),
    path('go_teacher_choice_title/', views.go_teacher_choice_title, name='go_teacher_choice_title'),
    path('teacher_choice_title_/', views.teacher_choice_title_, name='teacher_choice_title_'),
    path('teacher_topic_number_/', views.teacher_topic_number_, name='teacher_topic_number_'),

    path('student_login/', views.student_login, name='student_login'),
    path('student_login_/', views.student_login_, name='student_login_'),
    path('student_register/', views.student_register, name='student_register'),
    path('student_choice_title/', views.student_choice_title, name='student_choice_title'),
    path('student_answer/', views.student_answer, name='student_answer'),
    path('student_answer_/', views.student_answer_, name='student_answer_'),
    path('answer_compared/', views.answer_compared, name='answer_compared'),
    path('text_process/', views.text_process, name='text_process'),
    path('student_choice_score/', views.student_choice_score, name='student_choice_score'),
    path('student_choice_see_score/', views.student_choice_see_score, name='student_choice_see_score'),
    path('student_choice_see_score_check/', views.student_choice_see_score_check, name='student_choice_see_score_check'),
    path('student_score/', views.student_score, name='student_score'),
    path('student_score_check/', views.student_score_check, name='student_score_check'),
    path('student_choice_score2/', views.student_choice_score2, name='student_choice_score2'),
]