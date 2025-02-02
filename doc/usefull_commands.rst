Assuming Project Directory is Working Directory

1. Install Repo Local

.. code-block:: bash
    /usr/bin/python3 -m pipx install -e . --force

2. Install dependencies from egginfo

.. code-block:: bash
    python setup.py egg_info
    pip install -r *.egg-info/requires.txt
    rm -r *.egg-info/

