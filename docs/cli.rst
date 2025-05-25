CLI
===

The CLI requires some extra dependencies to function. Make sure to install zipline.py with the ``cli`` extra if you want to use the CLI.

.. code-block:: bash

   pip install "zipline.py[cli]"

The CLI is fully documented. Use the following command to list all subcommands.

.. code-block:: bash

   ziplinepy --help

The CLI also supports autocompletion for select shells. Use the following command(s) to generate an autocompletion script.

.. code-block:: bash

   ziplinepy --show-completion # prints the completion script
   ziplinepy --install-completion # attempts to install the completion script into your current shell

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
