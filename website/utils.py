def merge_users(user_1, user_2):
    """
    Merges the second user into the last user. Values of the first user get precedence.
    """
    # Model fields that we can directly merge
    model_fields = ['email', 'first_name', 'last_name',]
    for field in model_fields:
        if not getattr(user_1, field):
            setattr(user_1, field, getattr(user_2, field))
    # Date fields
    # We take the older joined date
    if user_2.date_joined < user_1.date_joined:
        user_1.date_joined = user_2.date_joined
    # We take the newer login date
    if user_2.last_login and user_1.last_login and user_2.last_login > user_1.last_login:
        user_1.last_login = user_2.last_login

    # Reverse foreign key fields, i.e. onetomany
    # We can simply change the reverse models foreign key to point to the new user and then save them
    reverse_foreign_managers = [
        'depositrecord_set',
        'inbox_set',
        'notificationarchive_set',
        'paper_set', # todolist
        'socialaccount_set',
        'uploadedpdf_set',
    ]
    for manager_name in reverse_foreign_managers:
        manager_1 = getattr(user_1, manager_name)
        manager_2 = getattr(user_2, manager_name)
        manager_1.add(*manager_2.all())


    # This are not straight forward managers, they could lead to double entries per repository
    repository_reverse_foreign_managers = [
        'haldepositpreferences_set',
        'osfdepositpreferences_set',
    ]
    for manager_name in repository_reverse_foreign_managers:
        manager_1 = getattr(user_1, manager_name)
        manager_2 = getattr(user_2, manager_name)
        # We want to use index, so we need lists
        objects_1 = list(manager_1.all().select_related('repository'))
        objects_2 = list(manager_2.all().select_related('repository'))
        for obj_2 in objects_2:
            try:
                i =  [obj.repository.pk for obj in objects_1].index(obj_2.repository.pk)
            except ValueError:
                # We do not have an objects for user_1, so we use that from user_2
                obj_2.user = user_1
                obj_2.save()
            else:
                # Go over fields and take value from user_2 if there's none for user_1
                obj_1 = objects_1[i]
                for field in obj_1._meta.get_fields():
                    if not getattr(obj_1, field.name):
                        setattr(obj_1, field.name, getattr(obj_2, field.name))
                obj_1.save()


    # This are more complicated one to one relations
    relations = [
        ('userpreferences', ['email', 'preferred_repository', 'last_repository'], 'user'),
    ]
    for relation_name, field_names, reverse_relation_name in relations:
        if not hasattr(user_1, relation_name):
            if hasattr(user_2, relation_name):
                # No object on user_1, but on user_2, so just change user
                relation_2 = getattr(user_2, relation_name)
                setattr(relation_2, reverse_relation_name, user_1)
                relation_2.save()
        else:
            if hasattr(user_2, relation_name):
                # Object for both, take values from user_2 only if non-existing for user_2
                relation_1 = getattr(user_1, relation_name)
                relation_2 = getattr(user_2, relation_name)
                for field_name in field_names:
                    field_1 = getattr(relation_1, field_name)
                    field_2 = getattr(relation_2, field_name)
                    if not field_1:
                        setattr(relation_1, field_name, field_2)
                relation_1.save()
