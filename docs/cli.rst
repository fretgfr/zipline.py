CLI
===

The CLI requires some extra dependencies to function. Make sure to install zipline.py with the ``cli`` extra if you want to use the CLI.

.. code-block:: bash

   # Windows
   py -m pip install "zipline.py[cli]"

   # Other platforms
   python3 -m pip install "zipline.py[cli]"

The CLI is fully documented. Use the following command to list all subcommands.

.. code-block:: bash

   ziplinepy --help

The CLI also supports autocompletion for select shells. Use the following command(s) to generate an autocompletion script.

.. code-block:: bash

   ziplinepy --show-completion # prints the completion script
   ziplinepy --install-completion # attempts to install the completion script into your current shell

The following environment variables are detected by the CLI, and will be used when set:

- ``ZIPLINE_SERVER`` (string)
   - The URL of your chosen Zipline instance.
- ``ZIPLINE_TOKEN`` (string)
   - An authentication token to use for API requests.
- ``ZIPLINE_PRINT_OBJECT`` (boolean)
   - Determines whether or not to print the full Python object returned by the zipline.py client.
   - Consider using the CLI arguments (usually ``--object`` or ``--text``) on specific commands to override this instead of a global environment variable, as the default behavior for commands using this changes depending on whether or not they are used in a TTY.
- ``ZIPLINE_VERBOSE`` (boolean)
   - Determines whether or not to print exception tracebacks when the application encounters an exception that it is meant to handle.
   - If the application encounters an unexpected exception, this option is ignored and the traceback will always be printed.

Example Usage
-------------

Uploading a file
^^^^^^^^^^^^^^^^

.. code-block:: bash

   ziplinepy upload \
       --server "https://zipline.example.com" \
       --token "$(cat /file/containing/zipline/token)" \
       file.png

Shortening a URL
^^^^^^^^^^^^^^^^

.. code-block:: bash

   ziplinepy shorten \
       --server "https://zipline.example.com" \
       --token "$(cat /file/containing/zipline/token)" \
       "https://github.com/fretgfr/zipline.py"
