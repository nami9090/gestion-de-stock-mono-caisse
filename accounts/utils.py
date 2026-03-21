
def redirect_user_by_role(user):
    if user.groups.filter(name='Admin').exists():
        return 'home'

    if user.groups.filter(name='Caisse').exists():
        return 'home_caisse'

    return 'access_denied'
