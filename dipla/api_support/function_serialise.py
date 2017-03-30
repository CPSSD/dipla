from base64 import b64encode
import dill


def get_encoded_script(func, input_script_template):
    """
    Takes in a function and a template and wraps the function in that
    template

    Returns:
        A base64 python script that executes the input function
    """
    pickle_code = serialise_code_object(func.__code__)
    b64_code = b64encode(pickle_code)
    filled_script = input_script_template.format(str(b64_code))
    return b64encode(bytes(filled_script, 'UTF-8')).decode('UTF-8')


def serialise_code_object(co):
    """
    Splits a code object into its parts and pickles them.

    Returns:
        A pickled tuple
    """
    # Note: These are in the order that types.CodeType's constructor takes.
    co_tuple = (
        co.co_argcount,
        co.co_kwonlyargcount,
        co.co_nlocals,
        co.co_stacksize,
        co.co_flags,
        co.co_code,
        co.co_consts,
        co.co_names,
        co.co_varnames,
        co.co_filename,
        co.co_name,
        co.co_firstlineno,
        co.co_lnotab,
        co.co_freevars,
        co.co_cellvars,
    )
    return dill.dumps(co_tuple)
