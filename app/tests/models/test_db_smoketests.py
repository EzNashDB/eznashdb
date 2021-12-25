def test_test_DB_smoketest(django_user_model):
    django_user_model.objects.create()
    assert django_user_model.objects.count() == 1
