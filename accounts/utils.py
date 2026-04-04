
def redirect_user_by_role(user):
    if user.groups.filter(name='Admin').exists():
        return 'dashboard:dashboard'

    if user.groups.filter(name='Caisse').exists():
        return 'dashboard:dashboard'

    return 'access_denied'
