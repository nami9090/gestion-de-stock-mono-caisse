from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader

from django.http import HttpResponse
from django.core.paginator import Paginator

from .utils import redirect_user_by_role
from .forms import UserCreateForm
from django.contrib.auth.models import User
from .models import UserActivityLog, Profile

from django.contrib import messages
from core.models import ShopSettings

from django.contrib.auth import authenticate, login, logout
from .decorators import role_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

import os


# Create your views here.
def login_view(request):
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
    return render(request, 'login_account.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@role_required('Admin')
def gestion_utilisateur(request):
    utilisateurs = User.objects.all().order_by('username')

    user_pagination = Paginator(utilisateurs, 20)
    pages_user = request.GET.get('pages_user')
    user_pages = user_pagination.get_page(pages_user)

    context = {
        'utilisateurs':user_pages
    }
    return render(request, 'gestion_utilisateur.html', context)

@login_required
@role_required('Admin')
def creer_utilisateur(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save()
            image = request.FILES.get('image')
            profile, created = Profile.objects.get_or_create(user=user)
            if image:
                profile.image = image
                profile.save()
            messages.success(
                request,
                f"L'utilisateur {user.username} a été créé avec succès !"
            )
            return redirect('user:gestion_utilisateur')
        else:
            messages.warning(request, "Erreur : le formulaire est invalide.")

    else:
        form = UserCreateForm()

    return render(request, 'form_utilisateur.html', {'form': form})

@login_required
@role_required('Admin')
def update_utilisateur(request, id):
    user = get_object_or_404(User, pk=id)

    #SAFE : évite crash si profile n'existe pas
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = UserCreateForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            # ================= PHOTO PROFILE =================
            image = request.FILES.get('image')

            if image:
                profile.image = image
                profile.save()

            messages.success(
                request,
                f"L'utilisateur {user.username} a été mis à jour avec succès !"
            )
            return redirect('user:gestion_utilisateur')
        else:
            messages.error(request, "Erreur : le formulaire est invalide.")
    else:
        form = UserCreateForm(instance=user)

    context = {
        'form': form,
        'edited_user': user,
        'profile': profile
    }
    return render(request, 'form_utilisateur.html', context)



@login_required
@role_required('Admin')
def supprimer_utilisateur(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.user == user:
        messages.warning(request, "Vous ne pouvez pas supprimer votre propre compte !")
        return redirect('user:gestion_utilisateur')

    if request.method == 'POST':

        username = user.username

        # ================= SUPPRESSION IMAGE PROFILE =================
        try:
            profile = user.profile
            if profile.image and profile.image.name != "profiles/default.png":
                if os.path.isfile(profile.image.path):
                    os.remove(profile.image.path)
        except:
            pass

        # ================= SUPPRESSION USER =================
        user.delete()

        messages.success(
            request,
            f"L'utilisateur {username} a été supprimé avec succès !"
        )

        return redirect('user:gestion_utilisateur')

    return render(request, 'confirm_delete_user.html', {'user': user})

@login_required
@role_required('Admin')
def activer_desactiver_utilisateur(request, id):
    user = get_object_or_404(User, pk=id)
    if request.user == user:
        messages.warning(request, "Vous ne pouvez desactiver votre propre compte")
        return redirect('user:gestion_utilisateur')

    user.is_active = not user.is_active
    user.save()
    messages.success(request, f"L'utilisateur {user.username} devient {user.is_active}")
    return redirect('user:gestion_utilisateur')

def user_activity(request, id):
    if not request.user.groups.filter(name__in=['Admin']).exists():
        raise PermissionDenied

    user_obj = get_object_or_404(User, pk=id)
    logs = UserActivityLog.objects.filter(user=user_obj).order_by('-created_at')

    log_pagination = Paginator(logs, 10)
    pages_log = request.GET.get('pages_log')
    log_pages = log_pagination.get_page(pages_log)

    context = {
        'user_obj': user_obj,
        'logs': log_pages
    }
    return render(request, "user_activity_details.html", context)