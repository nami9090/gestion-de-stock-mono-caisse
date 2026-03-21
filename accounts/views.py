from django.shortcuts import render, redirect
from django.template import loader

from django.http import HttpResponse

from .utils import redirect_user_by_role
from .forms import UserCreateForm
from .models import UserActivityLog

from django.contrib import messages

from core.models import ShopSettings
from core.forms import ShopSettingsForm

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