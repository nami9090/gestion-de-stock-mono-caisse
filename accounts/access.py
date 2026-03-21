
def user_has_role(user, role_name):
	return user.is_authenticated and user.groups.filter(name=role_name).exists()

def user_has_any_role(user, roles):
	return user.is_authenticated and user.groups.filter(name__in=roles).exists()

def user_has_all_role(user, roles):
	return all(
		user.groups.filter(name=roles).exists()
		for role in roles
	)