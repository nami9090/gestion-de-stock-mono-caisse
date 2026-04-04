from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader

from django.http import HttpResponse
from django.core.paginator import Paginator

from .utils import redirect_user_by_role
from .forms import UserCreateForm
from .models import UserActivityLog, User

from django.contrib import messages
from core.models import ShopSettings
from core.forms import ShopSettingsForm
from django.contrib.auth import authenticate, login, logout
from .decorators import role_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout


# Create your views here.
def login_view(request):
    template = loader.get_template('login_account.html')
    # if request.user.is_authenticated:
    #   return redirect(redirect_user_by_role(user))
    # template = loader.get_template('login.html')
    shop = ShopSettings.objects.first()
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username = username,
            password = password
        )
        if user is not None:
            login(request, user)
            redirect_url = redirect_user_by_role(user)
            return redirect(redirect_url)
        else:
            messages.warning(request, 'Email ou mot de pass incorect')

    context = {
        'shop':shop
    }
    return HttpResponse(template.render(context, request))

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@role_required('Admin')
def gestion_utilisateur(request):
    template = loader.get_template('gestion_utilisateur.html')
    utilisateurs = User.objects.all().order_by('username')

    user_pagination = Paginator(utilisateurs, 10)
    pages_user = request.GET.get('pages_user')
    user_pages = user_pagination.get_page(pages_user)

    context = {
        'utilisateurs':user_pages
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def creer_utilisateur(request):
    template = loader.get_template('form_utilisateur.html')
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"L'utilisateur {user.username} a été créé avec succès !")
            redirect('user:gestion_utilisateur')
        else:
            messages.error(request, "Erreur : le formulaire est invalide.")
    else:
        form = UserCreateForm()
        redirect('user:gestion_utilisateur')
    context = {
        'form':form
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def update_utilisateur(request, id):
    template = loader.get_template('form_utilisateur.html')
    user = get_object_or_404(User, pk=id)
    if request.method == 'POST':
        form = UserCreateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"L'utilisateur {user.username} a été updated avec succès !")
            redirect('user:gestion_utilisateur')
        else:
            messages.error(request, "Erreur : le formulaire est invalide.")
    else:
        form = UserCreateForm(instance=user)
        redirect('user:gestion_utilisateur')
    context = {
        'form':form
    }
    return HttpResponse(template.render(context, request))

@login_required
@role_required('Admin')
def supprimer_utilisateur(request, user_id):
    template = loader.get_template('confirm_delete_user.html')
    user = get_object_or_404(User, id=user_id)
    if request.user == user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte !")
        return redirect('user:gestion_utilisateur')
    
    if request.method == 'POST':
        user.delete()
        messages.success(request, f"L'utilisateur {user.username} a été supprimé avec succès !")
        return redirect('user:gestion_utilisateur')
    context = {
        'user':user
    }
    return render(request, 'confirm_delete_user.html', context)

@login_required
@role_required('Admin')
def activer_desactiver_utilisateur(request, id):
    user = get_object_or_404(User, pk=id)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, f"L'utilisateur {user.username} devient {user.is_active}")
    return redirect('user:gestion_utilisateur')