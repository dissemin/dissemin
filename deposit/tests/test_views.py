from deposit.views import get_all_repositories_and_protocols

class TestDepositView():
    """
    Class to group tests for deposit views
    """
    def test_get_all_repositories_and_protocols(self, repository, book_god_of_the_labyrinth, user_isaac_newton):
        """
        Shall return enabled repositories only.
        """
        for i in range(1,3):
            repository.dummy_repository()
        for i in range(1,3):
            repo = repository.dummy_repository()
            repo.enabled=False
            repo.save()

        result = get_all_repositories_and_protocols(book_god_of_the_labyrinth, user_isaac_newton)
        for r in result:
            assert r[0].enabled == True

