from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.db import IntegrityError
from .models import Project,Task
from django.contrib.auth.decorators import login_required
from datetime import datetime,date,timedelta
from django.http import JsonResponse
import json
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
# Create your views here.

def SignUpView(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.warning(request, 'Passwords must match.')
            return redirect('register')
        if User.objects.filter(email=email):
            messages.warning(request, 'Email already taken.')
            return redirect('register')
        try:        
            validate_password(password)
        except ValidationError:
            messages.error(request, "You password cannot be entirely numeric and must be atleast 8 characters long.")
            return redirect('register')
        
        try:
            user = User.objects.create_user(username, email, password)
            user.is_active=False
            user.save()
            
        except IntegrityError:
            messages.error(request, 'Username already taken.')
            return redirect('register')
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = request.build_absolute_uri(f'/activation/{token}/{uid}')
        email_subject = "Activate your account"
        email_body = render_to_string('activation_email.html',{'activation_link':activation_link})
        email = EmailMultiAlternatives(email_subject, '', to=[user.email])
        email.attach_alternative(email_body, 'text/html')
        email.send()
        messages.success(request, "Your account has been created. Please check your email to activate your account.")
        return redirect('register')
    
    else:
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'register.html')

def activate(request, uid, token):
    try:
        pk = urlsafe_base64_decode(uid).decode()
        user = User._default_manager.get(pk=pk)
    except(User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user,token):
        user.is_active = True
        user.save()
        login(request,user)
        return redirect('dashboard')
    else:
        messages.warning(request, "An error occurred while processing your request.")
        return redirect('login')

def LoginView(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request,'Invalid username or password')
            return redirect('login')
    
    else:
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'login.html')

def LogoutView(request):
    logout(request)
    return redirect('index')

def IndexView(request):
    return render(request, 'index.html')

@login_required
def CreateProjectView(request):
    if request.method == 'POST':
        title = request.POST['project_name']
        description = request.POST['description']
        deadline = request.POST['due_date']

        today = timezone.now().date()
        deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()

        if deadline_date < today:
            messages.warning(request, "Your project deadline is behind today's date.")
            return redirect('create_project')

        project_created = Project.objects.create(user=request.user, title=title, description=description, deadline=deadline, status='in_progress')

        return redirect('project_detail', project_id=project_created.id)
    
    else:
        return render(request, 'create_project.html')

@login_required  
def DashboardView(request):
    projects = Project.objects.filter(user=request.user).order_by('deadline')
    today = timezone.now().date()
    
    upcoming_days = 7
    upcoming_date = timezone.now().date() + timedelta(days=upcoming_days)

    upcoming_projects = Project.objects.filter(user=request.user, deadline__lte=upcoming_date, status__in = ['in_progress']).order_by('deadline')

    overdue_projects = Project.objects.filter(user=request.user, deadline__lt=today, status__in = ['in_progress','overdue']).order_by('deadline')
    for op in overdue_projects:
        if op.status != 'overdue':
            op.status = 'overdue'
            op.save()

    return render(request, 'dashboard.html', {
    'projects': projects, 
    'completed_projects': Project.objects.filter(user=request.user, status='completed').order_by('deadline'), 
    'ongoing_projects': Project.objects.filter(user=request.user, status='in_progress').order_by('deadline'), 
    'upcoming_projects': upcoming_projects,
    'overdue_projects': overdue_projects})

@login_required
def ProjectDetailsView(request, project_id):
    try:
        project = Project.objects.get(id=project_id, user=request.user)
        unmarked_overdue_tasks = Task.objects.filter(project=project, deadline__lt=timezone.now().date(), status__in=['in_progress'])
        if unmarked_overdue_tasks:
            for uot in unmarked_overdue_tasks:
                uot.status = 'overdue'
                uot.save()
        all_tasks = Task.objects.filter(project=project).order_by('deadline')
        completed_tasks = all_tasks.filter(status = 'completed')
        overdue_tasks = all_tasks.filter(status = 'overdue')
        ongoing_tasks = all_tasks.filter(status = 'in_progress')
        
        return render(request, 'project_detail.html', {'project': project, 'tasks': all_tasks, 'completed_tasks': completed_tasks, 'overdue_tasks': overdue_tasks, 'ongoing_tasks':ongoing_tasks})
    except Project.DoesNotExist:
        messages.error(request, "This project does not exist.")
        return redirect('dashboard')

@login_required
def CreateTaskView(request, project_id):
    try:
        project = Project.objects.get(id=project_id, user=request.user)
        if project.status == 'completed':
            messages.error(request, "The project for which you are trying to assign tasks is already completed.")
            return redirect('project_detail', project_id=project_id)
        if project.status == 'overdue':
            messages.error(request, "This project is overdue. You cannot assign any tasks to it. Extend the project's deadline to assign tasks.")
            return redirect('project_detail', project_id=project_id)
        if request.method == 'POST':
            title = request.POST['task_name']
            deadline = request.POST['task_due_date']
            priority = request.POST['task_priority']
            depends_on = request.POST['depends_on']

            today = timezone.now().date()

            deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()

            if deadline_date > project.deadline:
                messages.warning(request, f'Your task deadline exceeds the deadline of your project which is at {project.deadline}.')
                return redirect('create_task', project_id=project_id)
            if deadline_date < today:
                messages.warning(request, "Your task deadline cannot be earlier than today's date.")
                return redirect('create_task', project_id=project_id)
            if Task.objects.filter(project=project, title=title).exists():
                messages.warning(request, "A task with the same title already exists.")
                return redirect('create_task', project_id=project_id)
            
            if depends_on!='none':
                dependency_task = Task.objects.get(id=depends_on)
                if deadline_date < dependency_task.deadline:
                    messages.warning(request, f"The task's deadline cannot be earlier than the deadline of the task it depends on which is at {dependency_task.deadline}.")
                    return redirect('create_task', project_id=project_id)
                Task.objects.create(project=project, title=title, deadline=deadline, priority=priority, status='in_progress', depends_on=dependency_task)
                return redirect(f"{reverse('project_detail', args=[project_id])}#task-lists")
            
            Task.objects.create(project=project, title=title, deadline=deadline, priority=priority, status='in_progress')

            return redirect(f"{reverse('project_detail', args=[project_id])}#task-lists")
        
        else:
            return render(request, 'create_task.html', {'ongoing_tasks': Task.objects.filter(project=project, status='in_progress')})
    except Project.DoesNotExist:
        messages.error(request, "The project for which you are trying to assign tasks does not exist.")
        return redirect('dashboard')
    
def CompleteTaskView(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error":"You must be logged in."},status=401)
    if request.method == 'PUT':
        data = json.loads(request.body)
        task_id = data.get("task_id","")
        try:
            task = Task.objects.get(id=task_id, project__user=request.user)
            if task.status == 'completed':
                return JsonResponse({"message": "This task is already completed."}, status=401)
            elif task.status == 'overdue':
                return JsonResponse({"message": "This task is overdue. To complete it update it's deadline."}, status=401)
            else:
                if not task.is_unlocked():
                    return JsonResponse({"message": "incomplete dependencies."}, status=401)
                
                task.status = 'completed'
                task.save()
                return JsonResponse({"message": "Task completed successfully"}, status=201)
        except Task.DoesNotExist:
            return JsonResponse({"error": "Task not found"}, status=404)
    else:
        return JsonResponse({"errror":"Wrong request."},status=401)

def DeleteTaskView(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "You must be logged in."}, status=401)
    if request.method == "DELETE":
        data = json.loads(request.body)
        task_id = data.get("task_id","")
        try:
            task = Task.objects.get(id=task_id, project__user=request.user)
            task.delete()
            return JsonResponse({"error": "Task deleted"}, status=201)
        except Task.DoesNotExist:
            return JsonResponse({"error": "Task not found"}, status=404)
    else:
        return JsonResponse({"errror":"Wrong request."},status=401)

def DeleteProjectView(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "You must be logged in"}, status=401)
    if request.method == "DELETE":
        data = json.loads(request.body)
        project_id = data.get("project_id","")
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            project.delete()
            return JsonResponse({"error": "Project deleted"}, status=201)
        except Project.DoesNotExist:
            return JsonResponse({"error": "Project not found"}, status=404)
    else:
        return JsonResponse({"errror":"Wrong request."},status=401)

@login_required
def EditProjectView(request, project_id):
    try:
        project = Project.objects.get(id=project_id, user=request.user)
        if project.status == 'completed':
            messages.error(request, "This project cannot be edited anymore.")
            return redirect('dashboard')
        if request.method == 'POST':
            deadline = request.POST['edit-deadline']
            description = request.POST['edit-description']

            today = timezone.now().date()
            deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()

            if deadline_date < today:
                messages.warning(request, "Your Project deadline is behind today's date.")
                return redirect('edit_project', project_id=project_id)

            project.deadline = deadline
            project.description = description
            if project.status == 'overdue':
                if deadline_date >= today:
                    project.status = 'in_progress'
            project.save()
            return redirect('project_detail', project_id=project_id)
        else:
            return render(request, 'edit_project.html', {'project': project})
    except:
        messages.error(request, "This project does not exist.")
        return redirect('dashboard')

def CompleteProjectView(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "You must be logged in."}, status=401)
    if request.method == 'PUT':
        data = json.loads(request.body)
        project_id = data.get("project_id","")
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            bool = True
            if project.status == 'completed':
                return JsonResponse({"message":"Project already completed"}, status=401)
            if project.status == 'overdue':
                return JsonResponse({"message":"Project is overdue. To complete it change the deadline"}, status=401)
            for t in project.task.all():
                if t.status != 'completed':
                    bool = False
            if bool == False:
                return JsonResponse({"message":"incomplete tasks."}, status=401)
            project.status = 'completed'
            project.save()
            return JsonResponse({"message":"Project successfully completed"}, status=201)
        except Project.DoesNotExist:
            return JsonResponse({"error": "Project not found."}, status=404)
    else:
        return JsonResponse({"error": "Wrong request"}, status=401) 

@login_required
def EditTaskView(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        project = Project.objects.get(id=task.project.id)
        if task.project.user != request.user:
            messages.error(request, "Task not found.")
            return redirect('dashboard')
        if task.status == 'completed':
            messages.error(request, "This task is already completed and cannot be edited.")
            return redirect('project_detail', project_id=task.project.id)
        if task.project.status == 'overdue':
            messages.error(request, "You cannot edit tasks of an overdue project. Extend the project's deadline to edit the tasks.")
            return redirect('project_detail', project_id=task.project.id)
        if request.method == "POST":
            task_name = request.POST['edit_task_name']
            deadline = request.POST['edit_task_due_date']
            priority = request.POST['edit_task_priority']
            depends_on = request.POST['edit_depends_on']

            today_date = timezone.now().date()
            deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()

            if deadline_date>task.project.deadline:
                messages.warning(request,f'!Your task deadline exceeds the deadline of your project which is at {task.project.deadline}.')
                return redirect('edit_task', task_id=task_id)
            if today_date>deadline_date:
                messages.warning(request,"Your task deadline is behind today's date.")
                return redirect('edit_task', task_id=task_id)
            if Task.objects.filter(project=project, title=task_name).exclude(id=task_id).exists():
                messages.warning(request, "A task with the same title already exists.")
                return redirect('edit_task', task_id=task_id)

            if depends_on!='none':
                dependency_task = Task.objects.get(id=depends_on)
                if deadline_date<dependency_task.deadline:
                    messages.warning(request, f"The task's deadline cannot be earlier than the deadline of the task it depends on which is at {dependency_task.deadline}.")
                    return redirect('edit_task', task_id=task_id)
                if dependency_task in task.dependent_tasks.all():
                    messages.error(request,"Invalid dependency! You cannot set this task as a dependency because it would create a circular dependency.")
                    return redirect('edit_task', task_id=task_id)
                task.depends_on = dependency_task
            else:
                task.depends_on = None
            task.title = task_name
            task.deadline = deadline
            task.priority = priority
            if task.status == 'overdue':
                if deadline_date >= today_date:
                    task.status = 'in_progress'
            task.save()
            return redirect(f"{reverse('project_detail', args=[task.project.id])}#task-lists")
        else:
            return render(request, 'edit_task.html', {"task": task, 'ongoing_tasks': Task.objects.filter(project=project, status='in_progress').exclude(id=task_id), 'task_dependency': task.depends_on})
    except:
        messages.error(request, "Task not found.")
        return redirect('dashboard')

def StartStopClockView(request):
    if not request.user.is_authenticated:
        return JsonResponse({'message': 'You must be logged in.'}, status=401)
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data.get("task_id","")
        try:
            task = Task.objects.get(id=task_id, project__user=request.user)
            if task.status == 'in_progress' and task.is_unlocked():
                if task.timer_started_at:
                    time_diff = task.stop_timer()
                    task.save()
                    project_time_calculation(task.project.id, time_diff)
                    return JsonResponse({'message': 'Timer has stopped.','time_spent':str(task.time_spent)}, status=201)
                task.start_timer()
                task.save()
                return JsonResponse({'message': 'Timer has started.'}, status=201)
            return JsonResponse({'message': 'This task is not eligible for time control.'}, status=401)
        except Task.DoesNotExist:
            return JsonResponse({'message': 'Task not found.'}, status=404)
    else:
        return JsonResponse({'message': 'Wrong request.'}, status=401)

def project_time_calculation(project_id, time):
    project = Project.objects.get(id=project_id)
    project.time_spent += time
    project.save()

def EmailforPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = request.build_absolute_uri(f'/password_reset/{token}/{uid}')
            email_subject = "Link for resetting password"
            email_body = render_to_string('password_reset_email.html',{'reset_link':reset_link})
            email = EmailMultiAlternatives(email_subject,'',to=[email])
            email.attach_alternative(email_body, 'text/html')
            email.send()
            messages.success(request,'An email for resetting your password has been sent.')
            return redirect('email_for_password')
        else:
            messages.error(request,'No account with this email exists.')
            return redirect('email_for_password')
    return render(request, 'email_for_password.html')

def PasswordReset(request, token, uid):
    try:
        id = urlsafe_base64_decode(uid).decode()
        user = User._default_manager.get(pk=id)
    except User.DoesNotExist:
        user = None
    if user is not None and default_token_generator.check_token(user,token):
        if request.method == "POST":
            new_password = request.POST['new_password']
            confirm_new_password = request.POST['confirm_new_password']
            if new_password!=confirm_new_password:
                messages.error(request, "You passwords do not match.")
                return redirect('password_reset', token=token, uid=uid)
            try:
                validate_password(password=new_password, user=user)
            except ValidationError:
                messages.error(request, "You password cannot be entirely numeric, must be atleast 8 characters long and cannot be similar to your username or password.")
                return redirect('password_reset', token=token, uid=uid)
            user.set_password(new_password)
            user.save()
            messages.success(request, "Your password has been successfully reset. Now login.")
            return redirect('login')
        return render(request, 'password_reset.html')
    