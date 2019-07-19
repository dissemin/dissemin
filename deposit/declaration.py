import logging
import sys

current_module = sys.modules[__name__]

logger = logging.getLogger('dissemin.' + __name__)


# The dict contains the available functions and a admin-friendly name
REGISTERED_DECLARATION_FUNCTIONS = {
    'declaration_darmstadt' : 'ULB Darmstadt',
}


def get_declaration_pdf(deposit_record):
    """
    This function creates for a given deposit the letter of declaration. If the does not succeed, it raises an exception.
    :param deposit: DepositRecord containing information for declaration
    :returns: BytesIO containing pdf or raises Exception
    """
    func = get_declaration_function(deposit_record.repository.letter_declaration)
    return func(deposit_record)


def get_declaration_function(func_name):
    """
    This function gets the function to generate a letter of declaration. If no function can be found, we raise AttributeError.
    :param func_name: Name of the function that is requested
    :returns: function or raises AttributeError
    """
    return getattr(current_module, func_name)


def declaration_darmstadt(deposit):
    """
    Takes a deposit and creates authors declaration for ULB Darmstadt and returns that.
    """
    pass
