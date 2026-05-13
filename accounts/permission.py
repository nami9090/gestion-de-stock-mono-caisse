def is_admin(user):
    return user.groups.filter(name="Admin").exists()

def is_caisse(user):
    return user.groups.filter(name="Caisse").exists()

def is_serveur(user):
    return user.groups.filter(name="Serveur").exists()

def is_cuisine(user):
    return user.groups.filter(name="Cuisine").exists()