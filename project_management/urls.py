from django.urls import path
from .views import SignUpView,IndexView,LoginView,LogoutView,CreateProjectView,DashboardView,ProjectDetailsView,CreateTaskView,CompleteTaskView,DeleteTaskView,DeleteProjectView,EditProjectView,CompleteProjectView,EditTaskView,StartStopClockView,activate,EmailforPassword,PasswordReset

urlpatterns = [
    path('', IndexView, name='index'),
    path('register', SignUpView, name='register'),
    path('login', LoginView, name='login'),
    path('logout', LogoutView, name='logout'),
    path('activation/<token>/<uid>', activate, name="activate"),
    path('dashboard', DashboardView, name='dashboard'),
    path('create_project', CreateProjectView, name='create_project'),
    path('project_detail/<int:project_id>', ProjectDetailsView, name='project_detail'),
    path('create_task/<int:project_id>', CreateTaskView, name='create_task'),
    path('edit_project/<int:project_id>', EditProjectView, name='edit_project'),
    path('edit_task/<int:task_id>', EditTaskView, name='edit_task'),
    path('email_for_password', EmailforPassword, name='email_for_password'),
    path('password_reset/<token>/<uid>', PasswordReset, name='password_reset'),

    # APIs
    path('complete_task', CompleteTaskView, name='complete_task'),
    path('delete_task', DeleteTaskView, name='delete_task'),
    path('delete_project', DeleteProjectView, name='delete_project'),
    path('complete_project', CompleteProjectView, name='complete_project'),
    path('start_stop_clock', StartStopClockView, name='start_stop_clock'),
]
