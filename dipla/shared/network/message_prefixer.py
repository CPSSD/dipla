

def prefix_message(message):
    """
    Prepares a message to be sent across a TCP connection by prefixing
    the message with its length and a colon.

    Examples:
    "hi" -> "2:hi"
    "foo" -> "3:foo"
    "hello" -> "5:hello"

    """
    return "{}:{}".format(len(message), message)
