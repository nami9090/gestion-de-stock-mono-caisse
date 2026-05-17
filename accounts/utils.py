
def redirect_user_by_role(user):
    if user.groups.filter(name='Admin').exists():
        return 'dashboard:dashboard_admin'

    if user.groups.filter(name='Caisse').exists():
        return 'dashboard:dashboard_caisse'

    if user.groups.filter(name='Serveur').exists():
        return 'dashboard:dashboard_serveur'

    if user.groups.filter(name='Cuisine').exists():
        return 'dashboard:dashboard_cuisine'

    return 'access_denied'
